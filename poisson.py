from scipy.stats import poisson

# Cac tham so
lambda_rate = 5   # so su kien trung binh moi đon vi thoi gian
t = 2             # thoi gian quan sat
k = 8             # so su kien muon tinh xac suat

# Poisson parameter (lamda*t)
lambda_t = lambda_rate * t

# Tinh xac suat p_k(t)
p_k = poisson.pmf(k, mu=lambda_t)

print(f"Xac suat co {k} su kien trong {t} đon vi thoi gian la: {p_k:.5f}")
