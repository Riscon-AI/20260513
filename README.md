# Fusion Alloy AI Screener

핵융합로용 차세대 내화 합금 후보를 빠르게 줄이기 위한 DuctGPT형 로컬 프로토타입이다. 자연어 목표를 입력하면 후보 조성을 생성하고, 공개 원소 물성 기반의 physics-informed surrogate로 연성, 고온 적합성, BCC 안정성, 저방사화 가능성, 제조 가능성을 점수화한다.

이 시스템은 실제 신소재 발견을 확정하는 도구가 아니라, DFT·CALPHAD·합성·인장시험으로 넘길 후보를 줄이는 1차 스크리닝 도구다.

## 실행

웹 앱:

```bash
cd fusion-material-ai
python3 server.py
```

브라우저에서 `http://127.0.0.1:8765`를 연다.

CLI 리포트:

```bash
cd fusion-material-ai
python3 run_screen.py \
  --prompt "W-rich low activation ductile BCC alloy for plasma-facing fusion reactor components; prefer W Ti V Zr Ta Nb; density < 15" \
  --samples 2500 \
  --top 25
```

결과 파일:

- `outputs/top_candidates.csv`
- `outputs/screening_report.md`
- `outputs/screening_result.json`


저장소를 내려받기
터미널 가능하면:

git clone https://github.com/riscon-ai/20260513.git
cd 20260513

프로젝트 폴더에서 실행
파일이 저장소 루트에 있으면:

python3 server.py --host 127.0.0.1 --port 8765

만약 fusion-material-ai 폴더 안에 있으면:

cd fusion-material-ai
python3 server.py --host 127.0.0.1 --port 8765

http://127.0.0.1:8765

파이썬 설치
python --version

## 현재 MVP가 하는 일

1. 자연어 프롬프트에서 원소군, W-rich, NbTa-rich, 저방사화, 연성, 밀도 제한을 추출한다.
2. W, Ta, Nb, Ti, V, Mo, Hf, Zr 중심의 내화 다원계 합금 후보를 생성한다.
3. 평균 융점, 밀도, VEC, 혼합 엔트로피, 원자 크기 불일치, 전기음성도 분산을 계산한다.
4. 연성, 고온 적합성, BCC 안정성, 저방사화 가능성, 합성 가능성, 제조 가능성을 점수화한다.
5. 불확실성과 위험 플래그를 붙여 DFT/실험 우선순위를 제안한다.

## 설계 기준

이 프로토타입은 Ames National Laboratory의 DuctGPT 보도자료와 Acta Materialia 논문 초록/요약에서 확인되는 구조를 참조했다. DuctGPT는 AtomGPT를 기반으로 재료 데이터에 맞게 조정하고, 내화 다원계 합금의 연성 예측과 후보 스크리닝에 사용된 것으로 설명되어 있다.

참고 자료:

- Ames National Laboratory, “DuctGPT demonstrates how AI can accelerate discovery of next-generation fusion materials”: https://www.ameslab.gov/news/ductgpt-demonstrates-how-ai-can-accelerate-discovery-of-next-generation-fusion-materials
- Acta Materialia, “DuctGPT: A Generative Transformer for Forward Screening of Ductile Refractory Multi-Principal Element Alloys”: https://doi.org/10.1016/j.actamat.2025.121763
- NIST, “AtomGPT: Atomistic Generative Pre-trained Transformer for Forward and Inverse Materials Design”: https://www.nist.gov/publications/atomgpt-atomistic-generative-pre-trained-transformer-forward-and-inverse-materials

## 중요한 한계

- 현재 코드는 실제 DuctGPT 모델이나 AtomGPT 가중치를 포함하지 않는다.
- 원소별 기초 물성과 휴리스틱 점수로 만든 대체 모델이다.
- 조사 손상, 핵변환, He/H 보유, swelling, 열피로, 용접성, 산화, 플라즈마 침식 데이터는 아직 반영하지 않았다.
- 결과는 실험 후보를 줄이는 참고값이지, 핵융합로 적용 가능성을 보증하지 않는다.

## 다음 구축 단계

1. 공개 HEA/내화 합금 연성 데이터셋과 내부 실험 데이터를 연결한다.
2. DFT 계산 파이프라인을 붙여 형성에너지, 탄성상수, DOS, 결함 에너지를 자동 산출한다.
3. 모델을 Gaussian Process, XGBoost, GNN 또는 AtomGPT 계열 모델로 교체한다.
4. 불확실성 기반 active learning으로 다음 실험 후보를 자동 제안한다.
5. 실험 결과를 데이터베이스에 회수해 모델을 주기적으로 재학습한다.
