from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.util import dpid_to_str
from pox.lib.util import str_to_dpid
from pox.lib.util import str_to_bool
from pox.lib.packet.arp import arp
from pox.lib.packet.ipv4 import ipv4
from pox.openflow.discovery import Discovery
import pox.lib.packet as pkt
import time

log = core.getLogger()

# We don't want to flood immediately when a switch connects.
# Can be overriden on commandline.
_flood_delay = 0

class L3Routing (object):
  def __init__ (self, connection, transparent):
    self.connection = connection
    self.transparent = transparent
    self.graph={}
    self.listSWitch=[]
    self.listHost=[]
    self.host={'1':3, '2':3, '3':3,'4':3}
    self.path=[]
    self.macToPort = {}

    # We want to hear PacketIn messages, so we listen
    # to the connection
    connection.addListeners(self)

    # We just use this to know when to log a helpful message
    self.hold_down_expired = _flood_delay == 0

  def _handle_PacketIn (self, event):
    """
    Handle packet in messages from the switch to implement above algorithm.
    """

    packet = event.parsed
    def dijkstra(graph,src,dest,visited=[],distances={},predecessors={}):
    # a few sanity checks
      if src not in graph:
        raise TypeError('the root of the shortest path tree cannot be found in the graph')
      if dest not in graph:
        raise TypeError('the target of the shortest path cannot be found in the graph')    
    # ending condition
      if src == dest:
        # We build the shortest path and display it
        pred=dest
        while pred != None:
            self.path.append(pred)
            pred=predecessors.get(pred,None) 
      else :     
        # if it is the initial  run, initializes the cost
        if not visited: 
            distances[src]=0
        # visit the neighbors
        for neighbor in graph[src] :
            if neighbor not in visited:
                new_distance = distances[src] + 1
                if new_distance < distances.get(neighbor,float('inf')):
                    distances[neighbor] = new_distance
                    predecessors[neighbor] = src
        # mark as visited
        visited.append(src)
        # now that all neighbors have been visited: recurse                         
        # select the non visited node with lowest distance 'x'
        # run Dijskstra with src='x'
        unvisited={}
        for k in graph:
            if k not in visited:
                unvisited[k] = distances.get(k,float('inf'))        
        x=min(unvisited, key=unvisited.get)
        dijkstra(graph,x,dest,visited,distances,predecessors)
    
    def flood (message = None):
      """ Floods the packet """
      msg = of.ofp_packet_out()
      if time.time() - self.connection.connect_time >= _flood_delay:
        # Only flood if we've been connected for a little while...

        if self.hold_down_expired is False:
          # Oh yes it is!
          self.hold_down_expired = True
          log.info("%s: Flood hold-down expired -- flooding",
              dpid_to_str(event.dpid))

        if message is not None: log.debug(message)
        #log.debug("%i: flood %s -> %s", event.dpid,packet.src,packet.dst)
        # OFPP_FLOOD is optional; on some switches you may need to change
        # this to OFPP_ALL.
        msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
      else:
        pass
        #log.info("Holding down flood for %s", dpid_to_str(event.dpid))
      msg.data = event.ofp
      msg.in_port = event.port
      self.connection.send(msg)
    if not self.transparent:
      if packet.type == packet.LLDP_TYPE or packet.dst.isBridgeFiltered():
        drop()
        return
    if packet.dst.is_multicast:
      flood()
    else:
      for l in core.openflow_discovery.adjacency:
        sw_src = l.__str__().split("->")[0].split(".")[0].split("-")[5][1].strip()
        port_src= l.__str__().split("->")[0].split(".")[1].strip()
        sw_dst = l.__str__().split("->")[1].split(".")[0].split("-")[5][1].strip()
        port_dst=l.__str__().split("->")[1].split(".")[1].strip()
        log.debug("SW src: %s SW dst: %s Port src: %s Port dst: %s" %(sw_src, sw_dst, port_src, port_dst))
        if sw_src in self.listSWitch:
          list = self.graph[sw_src]
          list[sw_dst]=int(port_src)
          self.graph[sw_src]=list
        else:
          tlist={}
          tlist[sw_dst]=int(port_src)
          self.graph[sw_src]= tlist
          self.listSWitch.append(sw_src)
      if isinstance (packet.next, arp):
        arp_packet = packet.find(pkt.arp)
        src_ip = arp_packet.protosrc.toStr().split(".")[3]
        dst_ip = arp_packet.protodst.toStr().split(".")[3]
        dpid = dpid_to_str(event.dpid).split("-")[5][1]
      if isinstance(packet.next, ipv4):
        ip_packet = packet.find(pkt.ipv4)
        if ip_packet is not None:
          src_ip = ip_packet.srcip.toStr().split(".")[3]
          dst_ip = ip_packet.dstip.toStr().split(".")[3]
      log.debug("IP src= %s IP dst= %s" %(src_ip, dst_ip))
      self.path=[]
      dijkstra(self.graph, dst_ip, src_ip)
      print self.path
      dpid = dpid_to_str(event.dpid).split("-")[5][1]
      for index in range(len(self.path)):
        if dpid is self.path[index]:
          if self.path[index] is self.path[-1]:
            msg = of.ofp_flow_mod()
            msg.match = of.ofp_match.from_packet(packet, event.port)
            msg.idle_timeout = 10
            msg.hard_timeout = 30
            msg.actions.append(of.ofp_action_output(port = self.host[dpid]))
            msg.data = event.ofp
            self.connection.send(msg)
          else:
            msg = of.ofp_flow_mod()
            msg.match = of.ofp_match.from_packet(packet, event.port)
            msg.idle_timeout = 10
            msg.hard_timeout = 30
            msg.actions.append(of.ofp_action_output(port = self.graph[self.path[index]][self.path[index+1]]))
            msg.data = event.ofp
            self.connection.send(msg)
          

class l3_routing (object):
  def __init__ (self, transparent):
    core.openflow.addListeners(self)
    self.transparent = transparent

  def _handle_ConnectionUp (self, event):
    log.debug("Connection %s" % (event.connection,))
    L3Routing(event.connection, self.transparent)


def launch (transparent=False, hold_down=_flood_delay):
  """
  Starts an L3 routing.
  """
  try:
    global _flood_delay
    _flood_delay = int(str(hold_down), 10)
    assert _flood_delay >= 0
  except:
    raise RuntimeError("Expected hold-down to be a number")

  core.registerNew(l3_routing, str_to_bool(transparent))
