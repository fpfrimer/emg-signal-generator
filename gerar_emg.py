import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal as sg
import struct

# ===== PARÂMETROS =====
fs = 1000          # Hz (1 kHz)
duration = 3.0     # segundos
n_samples = int(fs * duration)
t = np.linspace(0, duration, n_samples, endpoint=False)

# ===== 1. GERAR SINAL EMG SINTÉTICO =====
np.random.seed(42)

# Ruído branco gaussiano
noise = np.random.randn(n_samples)

# Filtro passa-banda 20-450 Hz (Butterworth 4ª ordem)
sos = sg.butter(4, [20/500, 450/500], btype='band', output='sos')
emg = sg.sosfiltfilt(sos, noise)

# ===== 2. ENVELOPE DE CONTRAÇÃO =====
# Padrão: repouso -> contração crescente -> sustentação -> relaxamento -> repouso
envelope = np.zeros(n_samples)
# Segmentos
n_rest_1 = int(0.5 * fs)
n_ramp_up = int(0.6 * fs)
n_hold = int(0.8 * fs)
n_ramp_down = int(0.6 * fs)
n_rest_2 = int(0.5 * fs)

# Garantir que soma bate
n_total = n_rest_1 + n_ramp_up + n_hold + n_ramp_down + n_rest_2
diff = n_samples - n_total
n_hold += diff  # ajuste

# Construir envelope
rest = np.zeros(n_rest_1)
ramp_up = np.linspace(0, 1, n_ramp_up)**1.5  # curva de contração
hold = np.ones(n_hold)
ramp_down = np.linspace(1, 0, n_ramp_down)**2  # relaxamento mais rápido
rest2 = np.zeros(n_rest_2)

envelope = np.concatenate([rest, ramp_up, hold, ramp_down, rest2])

# Amplitude de pico (~±1.5 mV = 1500 µV para contração forte)
amp_peak = 0.0015  # Volts
emg_scaled = emg * envelope * amp_peak / np.std(emg)

# Verificar amplitude
print(f"Amplitude pico-a-pico: {np.ptp(emg_scaled)*1e6:.0f} µV")
print(f"RMS (contração): {np.std(emg_scaled[envelope > 0.5])*1e6:.0f} µV")

# ===== 3. PLOT =====
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 7), gridspec_kw={'height_ratios': [3, 1]})

ax1.plot(t, emg_scaled * 1e6, linewidth=0.6, color='#2ecc71')
ax1.set_ylabel('Amplitude (\u00b5V)', fontsize=12)
ax1.set_title('Sinal EMG Sint\u00e9tico — 20-450 Hz, 16 bits, 1 kHz', 
              fontsize=13, fontweight='bold')
ax1.set_xlim(0, duration)
ax1.grid(True, alpha=0.3)

# Envelope abaixo
ax2.fill_between(t, envelope * 100, alpha=0.3, color='#3498db')
ax2.plot(t, envelope * 100, linewidth=1, color='#3498db')
ax2.set_ylabel('For\u00e7a (%)', fontsize=12)
ax2.set_xlabel('Tempo (s)', fontsize=12)
ax2.set_xlim(0, duration)
ax2.set_ylim(0, 110)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('/home/hermes/emg_sintetico.png', dpi=150)
print("\nGráfico salvo!")

# ===== 4. GERAR HEADER C PRA DAC =====
# Escalar para int16 (range do DAC típico)
# Vamos assumir DAC de 12 bits (0-4095) com referência 3.3V
# Ou int16 para DAC externo
dac_ref = 3.3       # Volts (referência do DAC)
dac_bits = 12        # resolução
dac_max = (1 << dac_bits) - 1  # 4095

# O sinal EMG está em Volts. Precisamos:
# EMG (V) -> Atenuador (ganho G) -> Módulo de aquisição (ADC do DUT)
# Para o DAC, vamos gerar em Volts, e o usuário ajusta o atenuador.
# Opção 1: int16 (para DAC externo tipo MCP4922, AD5760, etc.)
# Opção 2: uint12 (para DAC interno do STM32/ESP32)

# Vou gerar os dois formatos

# Opção 1: int16 (bipolar) - mais versátil
# Escalar para ±1V na saída do DAC (ajustável pelo usuário)
v_ref_dac = 1.0  # ±1V na saída do DAC
emg_int16 = np.clip(emg_scaled / v_ref_dac * 32767, -32768, 32767).astype(np.int16)

# Opção 2: uint12 para DAC STM32 (unipolar 0-3.3V com offset)
# Adicionar offset de 1.65V (metade da referência)
emg_offset = emg_scaled / 2  # reduz amplitude para caber no range
emg_offset = emg_offset + 1.65  # deslocar para 0-3.3V
emg_uint12 = np.clip(emg_offset / 3.3 * 4095, 0, 4095).astype(np.uint16)

# Salvar arquivos
# Header C com array int16
with open('/home/hermes/emg_signal_int16.h', 'w') as f:
    f.write(f'// Sinal EMG sintético\n')
    f.write(f'// Taxa: {fs} Hz\n')
    f.write(f'// Duração: {duration} s\n')
    f.write(f'// Amostras: {len(emg_int16)}\n')
    f.write(f'// Amplitude: ±{v_ref_dac} V (ajustar atenuador)\n')
    f.write(f'// Banda: 20-450 Hz\n')
    f.write(f'// Formato: int16 (little-endian)\n\n')
    f.write(f'#define EMG_FS {fs}\n')
    f.write(f'#define EMG_N_SAMPLES {len(emg_int16)}\n')
    f.write(f'#define EMG_VREF {v_ref_dac}f\n\n')
    f.write(f'const int16_t emg_signal[{len(emg_int16)}] = {{\n')
    for i, val in enumerate(emg_int16):
        if i % 8 == 0:
            f.write('    ')
        f.write(f'{val:6d}, ')
        if i % 8 == 7:
            f.write('\n')
    if len(emg_int16) % 8 != 0:
        f.write('\n')
    f.write('};\n')

# Header C com array uint12 para STM32/ESP32
with open('/home/hermes/emg_signal_uint12.h', 'w') as f:
    f.write(f'// Sinal EMG sintético - formato uint12 (DAC interno MCU)\n')
    f.write(f'// Taxa: {fs} Hz\n')
    f.write(f'// Duração: {duration} s\n')
    f.write(f'// Amostras: {len(emg_uint12)}\n')
    f.write(f'// Range: 0-{dac_max} (0-{dac_ref}V)\n')
    f.write(f'// Banda: 20-450 Hz\n')
    f.write(f'// Formato: uint16 (usar 12 bits superiores para DAC)\n\n')
    f.write(f'#define EMG_FS {fs}\n')
    f.write(f'#define EMG_N_SAMPLES {len(emg_uint12)}\n')
    f.write(f'#define EMG_DAC_MAX {dac_max}\n\n')
    f.write(f'const uint16_t emg_signal[{len(emg_uint12)}] = {{\n')
    for i, val in enumerate(emg_uint12):
        if i % 8 == 0:
            f.write('    ')
        f.write(f'{val:5d}, ')
        if i % 8 == 7:
            f.write('\n')
    if len(emg_uint12) % 8 != 0:
        f.write('\n')
    f.write('};\n')

print(f"\nHeader C gerado: /home/hermes/emg_signal_int16.h ({len(emg_int16)} amostras)")
print(f"Header C gerado: /home/hermes/emg_signal_uint12.h ({len(emg_uint12)} amostras)")

# Também salvar raw binário
emg_int16.tofile('/home/hermes/emg_signal_int16.raw')
print(f"Raw binário: /home/hermes/emg_signal_int16.raw ({len(emg_int16)*2} bytes)")

# Stats finais
print(f"\n--- Info do sinal ---")
print(f"RMS da contração: {np.std(emg_scaled[envelope > 0.5])*1e6:.0f} µV")
print(f"Pico: {emg_scaled.max()*1e6:.0f} µV")
print(f"Vale: {emg_scaled.min()*1e6:.0f} µV")
print(f"Relação sinal-ruído de repouso: {(np.std(emg_scaled[envelope > 0.5]) / np.std(emg_scaled[envelope < 0.01])):.1f}x")
