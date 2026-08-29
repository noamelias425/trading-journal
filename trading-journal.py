import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime

# הגדרת דף
st.set_page_config(
    page_title="Trading Journal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DATA_FILE = "trades.csv"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df_loaded = pd.read_csv(DATA_FILE)
            if not df_loaded.empty:
                if "ID" not in df_loaded.columns:
                    df_loaded.insert(0, "ID", range(1, len(df_loaded) + 1))
                df_loaded["Notes"] = df_loaded["Notes"].fillna("").astype(str)
                df_loaded["Ticker"] = df_loaded["Ticker"].fillna("").astype(str)
                df_loaded["Strategy"] = df_loaded["Strategy"].fillna("").astype(str)
                df_loaded["Direction"] = df_loaded["Direction"].fillna("Long").astype(str)
                df_loaded["ID"] = df_loaded["ID"].astype(int)
            return df_loaded
        except Exception:
            pass
            
    return pd.DataFrame(columns=[
        "ID", "Date", "Ticker", "Direction", "Strategy", 
        "Entry", "Stop_Loss", "Exit", "Quantity", 
        "PnL", "R_Multiple", "Notes"
    ])

def save_data(df_to_save):
    df_to_save.to_csv(DATA_FILE, index=False)

df = load_data()

# התאמת CSS למובייל ול-Safari (כפתורים גדולים, ריווחים מותאמים)
st.markdown("""
<style>
    /* עיצוב מותאם לאייפון ומובייל */
    .metric-card {
        background-color: #1E222D;
        border-radius: 12px;
        padding: 14px;
        border: 1px solid #2A2E39;
        text-align: center;
        margin-bottom: 8px;
    }
    .big-stat { font-size: 22px; font-weight: bold; }
    .green { color: #089981; }
    .red { color: #F23645; }
    
    /* התאמת גודל כפתורים למגע */
    .stButton>button {
        width: 100%;
        min-height: 48px;
        font-size: 16px;
        border-radius: 8px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 14px;
        font-size: 15px;
    }
</style>
""", unsafe_allow_html=True)

st.title("📈 יומן מסחר")

tab_dashboard, tab_add, tab_edit, tab_table = st.tabs([
    "📊 דשבורד", 
    "➕ הזנה", 
    "✏️ עריכה/מחיקה", 
    "📋 עסקאות"
])

# ======================= דשבורד =======================
with tab_dashboard:
    if not df.empty:
        total_trades = len(df)
        winning_trades = len(df[df["PnL"] > 0])
        losing_trades = len(df[df["PnL"] < 0])
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        total_pnl = df["PnL"].sum()
        avg_r = df["R_Multiple"].mean()
        
        gross_profit = df[df["PnL"] > 0]["PnL"].sum()
        gross_loss = abs(df[df["PnL"] < 0]["PnL"].sum())
        profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else (gross_profit if gross_profit > 0 else 0)

        # כרטיסיות נתונים שמתאימות אוטומטית למובייל
        k1, k2 = st.columns(2)
        pnl_color = "green" if total_pnl >= 0 else "red"
        k1.markdown(f'<div class="metric-card"><div>רווח/הפסד כולל</div><div class="big-stat {pnl_color}">${total_pnl:,.2f}</div></div>', unsafe_allow_html=True)
        k2.markdown(f'<div class="metric-card"><div>Win Rate</div><div class="big-stat">{win_rate:.1f}%</div></div>', unsafe_allow_html=True)
        
        k3, k4, k5 = st.columns(3)
        k3.markdown(f'<div class="metric-card"><div>Avg R</div><div class="big-stat">{avg_r:+.2f}R</div></div>', unsafe_allow_html=True)
        k4.markdown(f'<div class="metric-card"><div>Profit Factor</div><div class="big-stat">{profit_factor}</div></div>', unsafe_allow_html=True)
        k5.markdown(f'<div class="metric-card"><div>עסקאות</div><div class="big-stat">{total_trades}</div></div>', unsafe_allow_html=True)

        st.markdown("---")

        # גרף צמיחה
        df["Cumulative_PnL"] = df["PnL"].cumsum()
        fig_equity = px.line(df, x="Date", y="Cumulative_PnL", title="📈 צמיחת תיק מצטברת ($)", markers=True)
        fig_equity.update_traces(line_color="#2962FF", line_width=3)
        fig_equity.update_layout(template="plotly_dark", plot_bgcolor="#131722", paper_bgcolor="#131722", margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_equity, use_container_width=True)

        # גרף R
        colors = ['#089981' if r >= 0 else '#F23645' for r in df["R_Multiple"]]
        fig_r = go.Figure(data=[go.Bar(x=df["Ticker"] + " (#" + df["ID"].astype(str) + ")", y=df["R_Multiple"], marker_color=colors)])
        fig_r.update_layout(title="🎯 תוצאות לפי R", yaxis_title="R", template="plotly_dark", plot_bgcolor="#131722", paper_bgcolor="#131722", margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_r, use_container_width=True)
    else:
        st.info("אין עדיין עסקאות. עבור ללשונית '➕ הזנה' כדי להתחיל.")

# ======================= הזנת עסקה =======================
with tab_add:
    st.subheader("➕ הזנת עסקה")
    with st.form("add_form", clear_on_submit=True):
        trade_date = st.date_input("תאריך", datetime.today())
        ticker = st.text_input("סימול מניה (Ticker)", placeholder="למשל: NVDA").upper().strip()
        direction = st.selectbox("כיוון", ["Long", "Short"])
        strategy = st.selectbox("סטאפ / אסטרטגיה", [
            "פריצה יומית/שבועית (Breakout)", 
            "בדיקת תמיכה (Pullback to EMA)", 
            "היפוך מגמה (Reversal)", 
            "אחר"
        ])

        c1, c2 = st.columns(2)
        entry_price = c1.number_input("מחיר כניסה ($)", min_value=0.0, step=0.01, format="%.2f")
        stop_loss = c2.number_input("סטופ לוס ($)", min_value=0.0, step=0.01, format="%.2f")
        
        c3, c4 = st.columns(2)
        exit_price = c3.number_input("מחיר יציאה ($)", min_value=0.0, step=0.01, format="%.2f")
        quantity = c4.number_input("כמות מניות", min_value=1, step=1, value=10)

        notes = st.text_area("הערות / סיבות לכניסה", placeholder="דגשים על הפוזיציה...")
        add_btn = st.form_submit_button("💾 שמור עסקה ביומן", use_container_width=True)

        if add_btn:
            if ticker and entry_price > 0 and exit_price > 0 and stop_loss > 0:
                if direction == "Long":
                    pnl = (exit_price - entry_price) * quantity
                    risk_per_share = entry_price - stop_loss
                else:
                    pnl = (entry_price - exit_price) * quantity
                    risk_per_share = stop_loss - entry_price

                total_risk = risk_per_share * quantity
                r_multiple = pnl / total_risk if total_risk > 0 else 0.0
                next_id = int(df["ID"].max() + 1) if not df.empty and "ID" in df.columns else 1

                new_row = {
                    "ID": next_id,
                    "Date": trade_date.strftime("%Y-%m-%d"),
                    "Ticker": str(ticker),
                    "Direction": str(direction),
                    "Strategy": str(strategy),
                    "Entry": float(entry_price),
                    "Stop_Loss": float(stop_loss),
                    "Exit": float(exit_price),
                    "Quantity": int(quantity),
                    "PnL": round(float(pnl), 2),
                    "R_Multiple": round(float(r_multiple), 2),
                    "Notes": str(notes)
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df)
                st.success(f"העסקה ב-{ticker} נשמרה בהצלחה!")
                st.rerun()
            else:
                st.error("נא למלא את כל השדות.")

# ======================= עריכה / מחיקה =======================
with tab_edit:
    st.subheader("✏️ עריכה או מחיקה")
    if df.empty:
        st.info("אין עסקאות לעריכה.")
    else:
        trade_options = {
            f"#{row['ID']} {row['Ticker']} ({row['Date']}) | ${row['PnL']}": row['ID'] 
            for _, row in df.iterrows()
        }
        selected_label = st.selectbox("בחר עסקה:", list(trade_options.keys()))
        selected_id = trade_options[selected_label]
        trade_data = df[df["ID"] == selected_id].iloc[0]

        with st.form("edit_form"):
            try:
                parsed_date = datetime.strptime(str(trade_data["Date"]), "%Y-%m-%d")
            except Exception:
                parsed_date = datetime.today()
                
            edit_date = st.date_input("תאריך", parsed_date)
            edit_ticker = st.text_input("סימול מניה", value=str(trade_data["Ticker"])).upper().strip()
            edit_direction = st.selectbox("כיוון", ["Long", "Short"], index=0 if trade_data["Direction"] == "Long" else 1)
            
            strategies = [
                "פריצה יומית/שבועית (Breakout)", 
                "בדיקת תמיכה (Pullback to EMA)", 
                "היפוך מגמה (Reversal)", 
                "אחר"
            ]
            strat_index = strategies.index(trade_data["Strategy"]) if trade_data["Strategy"] in strategies else 0
            edit_strategy = st.selectbox("סטאפ / אסטרטגיה", strategies, index=strat_index)

            c1, c2 = st.columns(2)
            edit_entry = c1.number_input("מחיר כניסה ($)", value=float(trade_data["Entry"]), min_value=0.0, step=0.01, format="%.2f")
            edit_sl = c2.number_input("סטופ לוס ($)", value=float(trade_data["Stop_Loss"]), min_value=0.0, step=0.01, format="%.2f")
            
            c3, c4 = st.columns(2)
            edit_exit = c3.number_input("מחיר יציאה ($)", value=float(trade_data["Exit"]), min_value=0.0, step=0.01, format="%.2f")
            edit_qty = c4.number_input("כמות מניות", value=int(trade_data["Quantity"]), min_value=1, step=1)

            edit_notes = st.text_area("הערות", value=str(trade_data["Notes"]))
            save_edit_btn = st.form_submit_button("🔄 שמור שינויים", use_container_width=True)

            if save_edit_btn:
                if edit_direction == "Long":
                    pnl = (edit_exit - edit_entry) * edit_qty
                    risk_per_share = edit_entry - edit_sl
                else:
                    pnl = (edit_entry - edit_exit) * edit_qty
                    risk_per_share = edit_sl - edit_entry

                total_risk = risk_per_share * edit_qty
                r_multiple = pnl / total_risk if total_risk > 0 else 0.0

                update_dict = {
                    "Date": edit_date.strftime("%Y-%m-%d"),
                    "Ticker": str(edit_ticker),
                    "Direction": str(edit_direction),
                    "Strategy": str(edit_strategy),
                    "Entry": float(edit_entry),
                    "Stop_Loss": float(edit_sl),
                    "Exit": float(edit_exit),
                    "Quantity": int(edit_qty),
                    "PnL": round(float(pnl), 2),
                    "R_Multiple": round(float(r_multiple), 2),
                    "Notes": str(edit_notes)
                }

                mask = df["ID"] == selected_id
                for col_k, val_v in update_dict.items():
                    df.loc[mask, col_k] = val_v

                save_data(df)
                st.success("העסקה עודכנה בהצלחה!")
                st.rerun()

        st.markdown("---")
        if st.button("🗑️ מחק עסקה זו לצמיתות", type="primary", use_container_width=True):
            df = df[df["ID"] != selected_id].reset_index(drop=True)
            save_data(df)
            st.warning("העסקה נמחקה.")
            st.rerun()

# ======================= טבלה =======================
with tab_table:
    st.subheader("📋 פירוט כל העסקאות")
    if not df.empty:
        st.dataframe(
            df.sort_values(by="ID", ascending=False),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("אין עסקאות להצגה.")