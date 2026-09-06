import io
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import requests
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="초등 장보기 미션 앱", page_icon="🛒", layout="wide"
)

# -------------------------------------------------------------------
# [세션 상태 초기화]
# -------------------------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = "start"
if "selected_mission" not in st.session_state:
    st.session_state.selected_mission = None
if "budget" not in st.session_state:
    st.session_state.budget = 0
if "cart" not in st.session_state:
    st.session_state.cart = {}  # {상품명: {"price": 가격, "qty": 수량, "img": url}}
if "submitted" not in st.session_state:
    st.session_state.submitted = False


# -------------------------------------------------------------------
# [데이터 로드 함수]
# -------------------------------------------------------------------
@st.cache_data
def load_products():
    try:
        df = pd.read_csv("products.csv")
        return df
    except Exception:
        # csv 파일이 없을 경우 대비한 샘플 데이터
        data = {
            "품명": [
                "카레용 돼지고기(300g)",
                "감자(1봉)",
                "당근(1개)",
                "양파(1망)",
                "카레 루(4인분)",
                "생일 케이크",
                "풍선 세트",
                "과자 모듬팩",
                "음료수(2L)",
                "꼬깔모자",
            ],
            "가격": [
                6000,
                3000,
                1200,
                2500,
                3500,
                22000,
                4000,
                8000,
                3000,
                2000,
            ],
            "이미지URL": [
                "https://images.unsplash.com/photo-1607623814075-e51df1bdc82f?w=300",
                "https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=300",
                "https://images.unsplash.com/photo-1447175008436-08417090ea9b?w=300",
                "https://images.unsplash.com/photo-1508747703725-719777637510?w=300",
                "https://images.unsplash.com/photo-1588166524941-3bf61a9c41db?w=300",
                "https://images.unsplash.com/photo-1535141192574-5d4897c13136?w=300",
                "https://images.unsplash.com/photo-1530103862676-de8c9debad1d?w=300",
                "https://images.unsplash.com/photo-1621939514649-280e2ee25f60?w=300",
                "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=300",
                "https://images.unsplash.com/photo-1513151233558-d860c5398176?w=300",
            ],
        }
        return pd.DataFrame(data)


# -------------------------------------------------------------------
# [결과 이미지 생성 함수]
# -------------------------------------------------------------------
def generate_result_image(mission_name, cart, total_spent, budget, reason):
    # 이미지 바탕 규격 (가로 800px, 세로 1000px)
    width, height = 800, 1000
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # 기본 폰트 로드 (폰트 깨짐 방지를 위해 PIL 기본 폰트 사용)
    font_large = ImageFont.load_default()
    font_medium = ImageFont.load_default()

    # 상단 헤더 배너
    draw.rectangle([0, 0, width, 100], fill=(70, 130, 180))
    draw.text(
        (30, 35),
        f"[미션] {mission_name}",
        fill=(255, 255, 255),
        font=font_large,
    )

    # 요약 정보
    y_pos = 130
    draw.text(
        (30, y_pos),
        f"총 예산: {budget:,}원  |  사용 금액: {total_spent:,}원  |  남은 돈: {budget - total_spent:,}원",
        fill=(0, 0, 0),
        font=font_medium,
    )

    y_pos += 40
    draw.line([(30, y_pos), (width - 30, y_pos)], fill=(200, 200, 200), width=2)

    # 구매 물건 목록
    y_pos += 20
    draw.text(
        (30, y_pos), "■ 구매한 물건 목록", fill=(0, 0, 0), font=font_medium
    )
    y_pos += 30

    for item, info in cart.items():
        if info["qty"] > 0:
            item_text = f"- {item} x {info['qty']}개 : {info['price'] * info['qty']:,}원"
            draw.text(
                (50, y_pos), item_text, fill=(50, 50, 50), font=font_medium
            )
            y_pos += 25

    y_pos += 20
    draw.line([(30, y_pos), (width - 30, y_pos)], fill=(200, 200, 200), width=2)

    # 구매 이유
    y_pos += 20
    draw.text(
        (30, y_pos), "■ 내가 이 물건들을 선택한 이유", fill=(0, 0, 0), font=font_medium
    )
    y_pos += 35

    # 텍스트 줄바꿈 처리
    lines = []
    words = reason.split(" ")
    current_line = ""
    for word in words:
        if len(current_line + word) > 40:
            lines.append(current_line)
            current_line = word + " "
        else:
            current_line += word + " "
    lines.append(current_line)

    for line in lines:
        draw.text((50, y_pos), line, fill=(30, 30, 30), font=font_medium)
        y_pos += 25

    # 이미지 데이터를 바이너리로 변환
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


# ===================================================================
# 1. 시작 화면
# ===================================================================
if st.session_state.page == "start":
    st.title("🛒 초등학생 알뜰 장보기 미션")
    st.subheader("오늘의 미션을 선택하고 합리적인 소비를 시작해보세요!")

    col1, col2 = st.columns(2)

    with col1:
        st.info("### 🍛 미션 1: 맛있는 카레 만들기")
        st.write("오늘 저녁 가족을 위해 카레를 만듭니다. 필요한 재료를 사보세요!")
        st.write("**예산: 15,000원**")
        if st.button("카레 만들기 미션 시작", key="m1"):
            st.session_state.selected_mission = "맛있는 카레 만들기"
            st.session_state.budget = 15000
            st.session_state.cart = {}
            st.session_state.page = "shop"
            st.rerun()

    with col2:
        st.success("### 🎂 미션 2: 친구 생일파티 준비하기")
        st.write("친구의 생일파티를 준비합니다. 파티용품과 음식을 챙겨보세요!")
        st.write("**예산: 40,000원**")
        if st.button("생일파티 미션 시작", key="m2"):
            st.session_state.selected_mission = "친구 생일파티 준비하기"
            st.session_state.budget = 40000
            st.session_state.cart = {}
            st.session_state.page = "shop"
            st.rerun()

# ===================================================================
# 2. 쇼핑 화면
# ===================================================================
elif st.session_state.page == "shop":
    st.title(f"🛍️ {st.session_state.selected_mission}")
    st.caption("필요한 상품의 수량을 선택하고 장바구니에 담으세요.")

    products_df = load_products()

    # 상품 진열 (3열 레이아웃)
    cols = st.columns(3)
    for idx, row in products_df.iterrows():
        col = cols[idx % 3]
        with col:
            st.image(row["이미지URL"], use_container_width=True)
            st.markdown(f"**{row['품명']}**")
            st.write(f"가격: {row['가격']:,}원")

            qty = st.number_input(
                "수량",
                min_value=0,
                max_value=10,
                value=st.session_state.cart.get(row["품명"], {}).get("qty", 0),
                key=f"qty_{idx}",
            )

            if st.button("장바구니 담기", key=f"btn_{idx}"):
                if qty > 0:
                    st.session_state.cart[row["품명"]] = {
                        "price": row["가격"],
                        "qty": qty,
                        "img": row["이미지URL"],
                    }
                    st.toast(f"{row['품명']} {qty}개가 장바구니에 담겼습니다!")
                elif row["품명"] in st.session_state.cart:
                    del st.session_state.cart[row["품명"]]
                    st.toast(f"{row['품명']}이(가) 장바구니에서 삭제되었습니다.")

    st.markdown("---")

    # [하단 장바구니 영역]
    st.subheader("🛒 내 장바구니")

    total_spent = sum(
        item["price"] * item["qty"] for item in st.session_state.cart.values()
    )
    budget = st.session_state.budget
    remaining = budget - total_spent

    # 예산 현황 출력
    col_b1, col_b2, col_b3 = st.columns(3)
    col_b1.metric("총 예산", f"{budget:,}원")
    col_b2.metric("현재 담은 금액", f"{total_spent:,}원")
    col_b3.metric("남은 돈", f"{remaining:,}원")

    # 담은 상품 목록 표시
    if st.session_state.cart:
        cart_summary = [
            f"- **{name}**: {info['qty']}개 ({info['price'] * info['qty']:,}원)"
            for name, info in st.session_state.cart.items()
            if info["qty"] > 0
        ]
        st.markdown("\n".join(cart_summary))
    else:
        st.info("장바구니가 비어 있습니다.")

    # 제출 및 예산 검증
    if total_spent > budget:
        st.error(
            f"⚠️ 예산을 {total_spent - budget:,}원 초과했습니다! 물건 수량을 줄여주세요."
        )
        st.button("제출하기", disabled=True)
    else:
        if st.button("제출하기", type="primary"):
            if total_spent == 0:
                st.warning("물건을 하나 이상 장바구니에 담아주세요!")
            else:
                st.session_state.submitted = True
                st.session_state.page = "result"
                st.rerun()

# ===================================================================
# 3. 결과 화면
# ===================================================================
elif st.session_state.page == "result":
    # 직접 접근 차단 guard
    if not st.session_state.submitted:
        st.session_state.page = "start"
        st.rerun()

    st.title("🎉 장보기 미션 완료!")
    st.subheader(f"미션 제목: {st.session_state.selected_mission}")

    total_spent = sum(
        item["price"] * item["qty"] for item in st.session_state.cart.values()
    )
    budget = st.session_state.budget
    remaining = budget - total_spent

    st.success(
        f"총 예산 **{budget:,}원** 중 **{total_spent:,}원**을 사용하여 **{remaining:,}원**이 남았습니다!"
    )

    st.markdown("### 📦 내가 구매한 물건들")
    for name, info in st.session_state.cart.items():
        if info["qty"] > 0:
            st.write(
                f"- **{name}** | {info['qty']}개 | {info['price'] * info['qty']:,}원"
            )

    st.markdown("---")

    # 구매 이유 입력
    reason = st.text_area(
        "💡 이 물건들을 선택한 이유를 작성해주세요:",
        placeholder="예: 예산 범위 안에서 카레 재료를 모두 준비하기 위해 양파와 감자의 수량을 조절했습니다.",
        height=120,
    )

    if reason.strip():
        # 이미지 생성
        img_bytes = generate_result_image(
            st.session_state.selected_mission,
            st.session_state.cart,
            total_spent,
            budget,
            reason,
        )

        st.download_button(
            label="🖼️ 결과 카드 그림으로 다운로드",
            data=img_bytes,
            file_name=f"장보기결과_{st.session_state.selected_mission}.png",
            mime="image/png",
            type="primary",
        )
    else:
        st.info("구매한 이유를 입력하면 다운로드 버튼이 활성화됩니다.")

    if st.button("처음으로 돌아가기"):
        st.session_state.page = "start"
        st.session_state.submitted = False
        st.rerun()
