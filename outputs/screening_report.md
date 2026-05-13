# Fusion Alloy AI Screening Report

Prompt: W-rich low activation ductile BCC alloy for plasma-facing fusion reactor components; prefer W Ti V Zr Ta Nb; density < 15

이 결과는 공개 원소 물성 기반의 physics-informed surrogate screening입니다. 실제 핵융합로 소재 후보로 채택하려면 DFT, CALPHAD, 조사 손상, 합성 및 인장시험 검증이 필요합니다.

## Top Candidates

| Rank | Candidate (at.%) | Score | Uncertainty | Recommendation | Key Risks |
| ---: | --- | ---: | ---: | --- | --- |
| 1 | W50Nb19.2V18.2Ti11.6Ta1 | 68.16 | 0.09 | 우선 DFT/소량 합성 후보 | 주요 플래그 없음 |
| 2 | W50.9Nb16Ti14.7V9.6Ta8.8 | 68.14 | 0.09 | 우선 DFT/소량 합성 후보 | 주요 플래그 없음 |
| 3 | W50.1Nb30.7Zr10.5Ti8.7 | 68.01 | 0.11 | 우선 DFT/소량 합성 후보 | 주요 플래그 없음 |
| 4 | W50.2V14.6Ti12.9Nb11.9Ta10.4 | 67.97 | 0.09 | 2차 계산 검증 후보 | 주요 플래그 없음 |
| 5 | W52.5Ti18.7Nb16.9V8.5Ta3.5 | 67.82 | 0.09 | 2차 계산 검증 후보 | 주요 플래그 없음 |
| 6 | W51.6Nb27V15.4Ta4.7Ti1.3 | 67.74 | 0.09 | 2차 계산 검증 후보 | 주요 플래그 없음 |
| 7 | W50.8Nb20.6Ta15.6V10.9Ti2.1 | 67.68 | 0.09 | 2차 계산 검증 후보 | 주요 플래그 없음 |
| 8 | W50.3Nb30.1Zr11.9Ta7.7 | 67.61 | 0.11 | 2차 계산 검증 후보 | 주요 플래그 없음 |
| 9 | W53.7Nb21.1V14.1Ti7.6Ta3.6 | 67.56 | 0.09 | 2차 계산 검증 후보 | 주요 플래그 없음 |
| 10 | W54.2Nb31Ti6.1Ta5.1V3.6 | 67.56 | 0.09 | 2차 계산 검증 후보 | 주요 플래그 없음 |
| 11 | W50.7Nb42.1Zr5Ti2.1 | 67.47 | 0.11 | 2차 계산 검증 후보 | 주요 플래그 없음 |
| 12 | W50.1Ti20.5Nb18.8Ta10.6 | 67.47 | 0.11 | 2차 계산 검증 후보 | 주요 플래그 없음 |
| 13 | W50.5Nb27.1V17.8Ti4.6 | 67.44 | 0.11 | 2차 계산 검증 후보 | 주요 플래그 없음 |
| 14 | W52.3Nb20.1Ti13.9Zr13.8 | 67.43 | 0.11 | 2차 계산 검증 후보 | 주요 플래그 없음 |
| 15 | W51.3Ta18Nb10.7V10.6Ti9.4 | 67.38 | 0.09 | 2차 계산 검증 후보 | 주요 플래그 없음 |

## Candidate Details

### W50Nb19.2V18.2Ti11.6Ta1

- Composition: {"W": 50.02, "Ta": 0.98, "Nb": 19.17, "Ti": 11.62, "V": 18.21}
- Descriptors: {"avg_melting_point_c": 2757.7245, "avg_density_g_cm3": 13.072, "avg_vec": 5.384, "avg_thermal_conductivity_w_mk": 105.5968, "mixing_entropy_r": 1.2688, "size_mismatch_percent": 3.1702, "electronegativity_spread": 0.3834, "refractory_fraction": 0.8838}
- Scores: {"ductility": 0.6224, "high_temperature": 0.7662, "bcc_stability": 0.9577, "low_activation": 0.6628, "synthesizability": 0.7644, "manufacturability": 0.5495, "density": 0.3928, "thermal_transport": 0.6114}
- Next tests: CALPHAD 또는 DFT로 형성에너지와 BCC 단상 안정성 확인; 고온 탄성상수, Cauchy pressure, Pugh ratio 등 연성 지표 계산; 소량 아크멜팅/분말공정 합성 후 XRD/SEM-EDS 상분석; 상온 및 고온 인장시험으로 연신율 검증; 중성자 조사, He/H 보유, swelling proxy 평가

### W50.9Nb16Ti14.7V9.6Ta8.8

- Composition: {"W": 50.905, "Ta": 8.819, "Nb": 15.998, "Ti": 14.699, "V": 9.579}
- Descriptors: {"avg_melting_point_c": 2832.4504, "avg_density_g_cm3": 13.8904, "avg_vec": 5.3621, "avg_thermal_conductivity_w_mk": 107.9501, "mixing_entropy_r": 1.3576, "size_mismatch_percent": 3.0028, "electronegativity_spread": 0.3963, "refractory_fraction": 0.853}
- Scores: {"ductility": 0.6112, "high_temperature": 0.8162, "bcc_stability": 0.9687, "low_activation": 0.6443, "synthesizability": 0.7718, "manufacturability": 0.5186, "density": 0.311, "thermal_transport": 0.6282}
- Next tests: CALPHAD 또는 DFT로 형성에너지와 BCC 단상 안정성 확인; 고온 탄성상수, Cauchy pressure, Pugh ratio 등 연성 지표 계산; 소량 아크멜팅/분말공정 합성 후 XRD/SEM-EDS 상분석; 상온 및 고온 인장시험으로 연신율 검증; 중성자 조사, He/H 보유, swelling proxy 평가

### W50.1Nb30.7Zr10.5Ti8.7

- Composition: {"W": 50.125, "Nb": 30.683, "Ti": 8.671, "Zr": 10.521}
- Descriptors: {"avg_melting_point_c": 2815.0931, "avg_density_g_cm3": 13.3556, "avg_vec": 5.3093, "avg_thermal_conductivity_w_mk": 107.5705, "mixing_entropy_r": 1.1576, "size_mismatch_percent": 4.4705, "electronegativity_spread": 0.4205, "refractory_fraction": 0.9133}
- Scores: {"ductility": 0.6202, "high_temperature": 0.8241, "bcc_stability": 0.9439, "low_activation": 0.661, "synthesizability": 0.711, "manufacturability": 0.5407, "density": 0.3644, "thermal_transport": 0.6255}
- Next tests: CALPHAD 또는 DFT로 형성에너지와 BCC 단상 안정성 확인; 고온 탄성상수, Cauchy pressure, Pugh ratio 등 연성 지표 계산; 소량 아크멜팅/분말공정 합성 후 XRD/SEM-EDS 상분석; 상온 및 고온 인장시험으로 연신율 검증; 중성자 조사, He/H 보유, swelling proxy 평가
