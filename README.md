# EMG Signal Generator

Gerador de sinais EMG sintéticos realistas para teste de módulos de aquisição biomédica.

## Visão geral

Este projeto gera sinais EMG de superfície sintéticos com características fisiológicas realistas:
- **Banda 20–450 Hz** (filtro Butterworth 4ª ordem)
- **Envelope de contração ajustável** (repouso → rampa → sustentação → relaxamento)
- **Amplitude escalável** em Volts
- **16 bits de resolução**

O sinal gerado pode ser reproduzido via **DAC + atenuador** para testar front-ends analógicos e ADCs de sistemas de aquisição de EMG.

## Como usar

```bash
python3 gerar_emg.py
```

Gera:
| Arquivo | Descrição |
|---|---|
| `emg_signal_int16.h` | Array C `int16_t[3000]` para DAC externo bipolar |
| `emg_signal_uint12.h` | Array C `uint16_t[3000]` para DAC interno (STM32/ESP32) |
| `emg_signal_int16.raw` | Binário raw (6000 bytes) para DMA |
| `emg_sintetico.png` | Plot do sinal + envelope |

## Cadeia de teste

```
Array C (int16) → DAC (1 kHz) → Atenuador (ganho G) → Módulo de aquisição (DUT)
```

## Parâmetros ajustáveis

Edite as variáveis no topo do `gerar_emg.py`:

| Parâmetro | Padrão | Descrição |
|---|---|---|
| `fs` | 1000 Hz | Taxa de amostragem |
| `duration` | 3.0 s | Duração total |
| `amp_peak` | 0.0015 V | Amplitude de pico (±1.5 mV) |
| `n_rest_1` | 500 | Amostras de repouso inicial |
| `n_ramp_up` | 600 | Amostras de subida |
| `n_hold` | 800 | Amostras de sustentação |
| `n_ramp_down` | 600 | Amostras de relaxamento |

## Documentação

A documentação detalhada da metodologia está em [`doc/metodologia.md`](doc/metodologia.md),
incluindo:

- Fundamentos fisiológicos do EMG
- Modelo matemático do sinal (ruído Gaussiano filtrado)
- Especificação do filtro Butterworth 20–450 Hz
- Modelo de envelope de contração (recrutamento de unidades motoras)
- Validação e limitações do modelo
- Referências bibliográficas (De Luca, Farina, Henneman, SENIAM, etc.)

## Dependências

- Python 3
- numpy
- scipy
- matplotlib (opcional, para o plot)

## Licença

MIT
