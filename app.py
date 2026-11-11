import json
import os
import re
from datetime import date, timedelta
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

st.set_page_config(page_title="Nexus | Business Operations", page_icon="◈", layout="wide", initial_sidebar_state="expanded")

# ---------- Theme ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root { --ink:#172033; --muted:#738096; --line:#e8edf4; --surface:#ffffff; --bg:#f5f7fb; --brand:#5b67e8; }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
.stApp { background:var(--bg); color:var(--ink); }
.block-container { padding-top:1.5rem; padding-bottom:2rem; max-width:1500px; }
[data-testid="stSidebar"] { background:#111a2c; }
[data-testid="stSidebar"] * { color:#e9edf7 !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] label { padding:8px 10px; border-radius:9px; }
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background:#25314a; }
.hero { display:flex; justify-content:space-between; align-items:center; gap:16px; margin-bottom:22px; }
.eyebrow { color:var(--brand); font-size:11px; font-weight:800; letter-spacing:1.5px; text-transform:uppercase; }
h1,h2,h3 { font-family:'Manrope',sans-serif !important; letter-spacing:-.5px; }
.hero h1 { font-size:28px; margin:4px 0 0; }
.subtle { color:var(--muted); font-size:13px; }
.kpi { background:white; border:1px solid var(--line); border-radius:15px; padding:17px 18px; min-height:118px; }
.kpi-label { color:var(--muted); font-size:12px; font-weight:600; }
.kpi-value { font-family:'Manrope'; font-size:27px; font-weight:800; margin:8px 0 3px; color:var(--ink); }
.kpi-foot { font-size:11px; color:#15966b; font-weight:700; }
.panel { background:white; border:1px solid var(--line); border-radius:15px; padding:18px; }
.panel-title { font-family:'Manrope'; font-size:15px; font-weight:800; margin-bottom:2px; }
.pill { display:inline-block; border-radius:20px; padding:4px 9px; font-size:11px; font-weight:700; background:#eef1ff; color:#525fe0; }
div[data-testid="stMetric"] { background:white; border:1px solid var(--line); border-radius:14px; padding:14px; }
.stButton button { border-radius:9px; font-weight:700; }
@media(max-width:700px) { .hero { align-items:flex-start; flex-direction:column; } .hero h1 {font-size:23px;} }
</style>
""", unsafe_allow_html=True)

# ---------- Demo data ----------
orders = pd.DataFrame({
    "Order": ["ORD-1048","ORD-1047","ORD-1046","ORD-1045","ORD-1044","ORD-1043"],
    "Customer": ["Aster Labs","Northstar Co.","Mira Retail","Urban Nest","Aster Labs","Bluepeak"],
    "Date": [date.today()-timedelta(days=i) for i in range(6)],
    "Amount (₹)": [48500, 32700, 18900, 12400, 56800, 22100],
    "Status": ["Processing","Delivered","Pending","Delivered","Processing","Cancelled"]
})
inventory = pd.DataFrame({
    "SKU":["SKU-1001","SKU-1002","SKU-1003","SKU-1004","SKU-1005","SKU-1006"],
    "Product":["Wireless Scanner","Thermal Printer","Packing Carton M","Barcode Labels","Handheld Terminal","Shipping Pouch"],
    "Category":["Hardware","Hardware","Packaging","Consumables","Hardware","Packaging"],
    "Stock":[42,8,240,14,5,180],
    "Reorder level":[15,12,60,25,10,50],
    "Unit price (₹)":[6500,8900,85,420,14500,12]
})
customers = pd.DataFrame({
    "Customer":["Aster Labs","Northstar Co.","Mira Retail","Urban Nest","Bluepeak"],
    "Segment":["Enterprise","SMB","Retail","SMB","Enterprise"],
    "Orders":[24,17,11,8,19],
    "Lifetime value (₹)":[425000,286000,142000,98000,354000],
    "Health":["Healthy","Healthy","At risk","Healthy","Healthy"]
})
shipments = pd.DataFrame({
    "Tracking ID":["TRK-88301","TRK-88302","TRK-88303","TRK-88304"],
    "Destination":["Kochi, KL","Bengaluru, KA","Chennai, TN","Coimbatore, TN"],
    "Carrier":["BlueDart","Delhivery","DTDC","BlueDart"],
    "ETA":["Today, 4:30 PM","Tomorrow","Today, 7:00 PM","Nov 13"],
    "Status":["In transit","Picked up","Delayed","Delivered"]
})

def header(title, description, tag="WORKSPACE"):
    st.markdown(f'<div class="hero"><div><div class="eyebrow">{tag}</div><h1>{title}</h1><div class="subtle">{description}</div></div></div>', unsafe_allow_html=True)

def panel_title(title, note=None):
    st.markdown(f'<div class="panel-title">{title}</div><div class="subtle" style="margin-bottom:12px">{note or ""}</div>', unsafe_allow_html=True)

def kpi(label, value, foot, color="#15966b"):
    st.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div class="kpi-foot" style="color:{color}">{foot}</div></div>', unsafe_allow_html=True)

def status_badge(status):
    palette = {"Delivered":"#e7f8f0;color:#16845e", "Processing":"#eef1ff;color:#525fe0",
               "Pending":"#fff5df;color:#a56b00", "Cancelled":"#fff0f0;color:#c44c4c",
               "In transit":"#eef1ff;color:#525fe0", "Picked up":"#fff5df;color:#a56b00",
               "Delayed":"#fff0f0;color:#c44c4c", "Healthy":"#e7f8f0;color:#16845e",
               "At risk":"#fff5df;color:#a56b00"}
    style = palette.get(status, "#f0f2f6;color:#5f6b7a")
    return f'<span style="background:{style.split(";")[0]};color:{style.split(";")[1].split(":")[1]};padding:4px 9px;border-radius:20px;font-size:11px;font-weight:700">{status}</span>'

def get_openai_api_key():
    if api_key := os.getenv("OPENAI_API_KEY"):
        return api_key
    try:
        return st.secrets["OPENAI_API_KEY"]
    except (KeyError, StreamlitSecretNotFoundError):
        return None

def request_openai_chat(api_key, model, messages):
    request = Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps({"model": model, "messages": messages}).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        try:
            error_body = json.loads(error.read().decode("utf-8"))
            api_error = error_body.get("error", {})
            message = api_error.get("message") if isinstance(api_error, dict) else None
        except (json.JSONDecodeError, UnicodeDecodeError):
            message = None
        raise RuntimeError(
            f"OpenAI request failed (HTTP {error.code}): {message or error.reason}"
        ) from error
    except URLError as error:
        raise RuntimeError(f"Could not connect to OpenAI: {error.reason}") from error
    except TimeoutError as error:
        raise RuntimeError("OpenAI request timed out after 30 seconds.") from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise RuntimeError("OpenAI returned an invalid response.") from error

    try:
        answer = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise RuntimeError("OpenAI response did not contain a chat message.") from error
    if not isinstance(answer, str) or not answer.strip():
        raise RuntimeError("OpenAI returned an empty response.")
    return answer

def demo_assistant_response(prompt):
    question = prompt.casefold()

    if re.search(r"\b(hello|hi|hey|help)\b", question):
        return (
            "Hi! I’m your dashboard assistant. I can answer questions about inventory, orders, "
            "revenue, customers, and shipments using the sample data. Try: "
            "**“Which items need reordering?”**"
        )

    if any(word in question for word in ("inventory", "stock", "reorder", "sku", "product")):
        low_stock = inventory[inventory["Stock"] <= inventory["Reorder level"]]
        if any(word in question for word in ("low", "reorder", "restock")):
            items = "; ".join(
                f'{row["Product"]}: {row["Stock"]} in stock (reorder at {row["Reorder level"]})'
                for _, row in low_stock.iterrows()
            )
            return f"{len(low_stock)} demo items are at or below their reorder level: {items}."
        return (
            f"The demo catalogue has {len(inventory)} products and "
            f"{int(inventory['Stock'].sum()):,} units in stock. "
            f"{len(low_stock)} products are at or below their reorder level."
        )

    if any(word in question for word in ("revenue", "sales", "income", "growth")):
        return "The dashboard's illustrative revenue is ₹18.42 lakh, up 12.8% versus last month."

    if "order" in question:
        status_counts = orders["Status"].value_counts()
        breakdown = ", ".join(f"{status}: {count}" for status, count in status_counts.items())
        return (
            f"The dashboard reports 248 active orders. The {len(orders)} recent demo orders "
            f"shown here break down as: {breakdown}."
        )

    if any(word in question for word in ("customer", "client", "segment")):
        at_risk = customers[customers["Health"] == "At risk"]["Customer"].tolist()
        return (
            f"The dashboard reports 1,284 customers. In the demo customer sample, "
            f"{', '.join(at_risk) if at_risk else 'no customers'} "
            "are marked at risk."
        )

    if any(word in question for word in ("shipment", "shipping", "delivery", "carrier", "tracking")):
        delayed = shipments[shipments["Status"] == "Delayed"]
        if delayed.empty:
            return f"There are {len(shipments)} demo shipments, and none are marked delayed."
        ids = ", ".join(delayed["Tracking ID"].tolist())
        return f"There are {len(shipments)} demo shipments. Delayed tracking ID(s): {ids}."

    return (
        "I can help with the sample dashboard's inventory, reorder items, orders, revenue, "
        "customers, and shipments. What would you like to know?"
    )

with st.sidebar:
    st.markdown("## ◈ NEXUS")
    st.caption("BUSINESS OPERATIONS PLATFORM")
    st.divider()
    page = st.radio("NAVIGATION", ["Overview","Inventory","Customers","Logistics","Analytics","AI Assistant","AI Control Center"], label_visibility="visible")
    st.divider()
    st.markdown("**WORKSPACE**")
    st.caption("Acme Commerce Pvt. Ltd.")
    st.caption("● All systems operational")
    st.markdown("---")
    st.caption("Demo workspace · v1.0")

# ---------- Overview ----------
if page == "Overview":
    header("Good morning, Archa & Shahin", "Here’s what’s happening across your business today.", "ADMIN DASHBOARD")
    c1,c2,c3,c4 = st.columns(4)
    with c1: kpi("TOTAL REVENUE","₹18.42L","↗ 12.8% vs last month")
    with c2: kpi("ACTIVE ORDERS","248","↗ 8.2% vs last month")
    with c3: kpi("CUSTOMERS","1,284","↗ 5.4% vs last month")
    with c4: kpi("FULFILMENT RATE","96.8%","↗ 2.1% vs last month")
    st.write("")
    left,right = st.columns([1.65,1], gap="large")
    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        panel_title("Revenue overview","Monthly revenue · illustrative demo data")
        rev = pd.DataFrame({"Month":["Jun","Jul","Aug","Sep","Oct","Nov"],"Revenue":[10.2,11.8,11.1,14.4,15.9,18.4]})
        fig = px.area(rev,x="Month",y="Revenue", markers=True)
        fig.update_traces(line_color="#626ee8", fillcolor="rgba(98,110,232,.12)")
        fig.update_layout(height=260,margin=dict(l=0,r=0,t=8,b=0),paper_bgcolor="white",plot_bgcolor="white",
                          xaxis_title="",yaxis_title="Revenue (₹ lakh)",font=dict(family="DM Sans",color="#738096"),
                          yaxis=dict(gridcolor="#edf0f5"),xaxis=dict(showgrid=False))
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        panel_title("Order status","Current order distribution")
        dist = pd.DataFrame({"Status":["Delivered","Processing","Pending","Cancelled"],"Orders":[142,68,28,10]})
        fig2 = px.pie(dist,names="Status",values="Orders",hole=.68,
                      color="Status",color_discrete_map={"Delivered":"#29b58a","Processing":"#626ee8","Pending":"#f1b84b","Cancelled":"#e47777"})
        fig2.update_layout(height=260,margin=dict(l=0,r=0,t=8,b=0),paper_bgcolor="white",showlegend=True,
                           legend=dict(orientation="h",y=-.12),font=dict(family="DM Sans",color="#738096"))
        st.plotly_chart(fig2,use_container_width=True,config={"displayModeBar":False})
        st.markdown('</div>', unsafe_allow_html=True)
    st.write("")
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    panel_title("Recent orders","Latest activity across your store")
    st.dataframe(orders, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ---------- Inventory ----------
elif page == "Inventory":
    header("Inventory management","Monitor stock, identify reorder risks and manage your catalogue.","OPERATIONS")
    low = int((inventory["Stock"] <= inventory["Reorder level"]).sum())
    a,b,c = st.columns(3)
    with a: kpi("TOTAL SKUs",f"{len(inventory):,}","Across all categories")
    with b: kpi("LOW STOCK ITEMS",str(low),"Requires replenishment","#c47b19")
    with c: kpi("STOCK UNITS",f'{inventory["Stock"].sum():,}',"Current on-hand quantity")
    st.write("")
    search = st.text_input("Search inventory", placeholder="Search by SKU or product name")
    view = inventory[inventory.astype(str).apply(lambda x: x.str.contains(search,case=False)).any(axis=1)] if search else inventory
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    panel_title("Product catalogue","Select a row to review stock levels")
    st.dataframe(view, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.write("")
    st.markdown("#### Reorder recommendations")
    for _,r in inventory[inventory["Stock"] <= inventory["Reorder level"]].iterrows():
        st.warning(f'{r["Product"]} · {r["Stock"]} units remaining (reorder level: {r["Reorder level"]})')
    with st.expander("＋ Add inventory item"):
        with st.form("add_inventory"):
            x1,x2 = st.columns(2)
            sku = x1.text_input("SKU")
            product = x2.text_input("Product name")
            stock = x1.number_input("Opening stock",min_value=0,step=1)
            reorder = x2.number_input("Reorder level",min_value=0,step=1)
            if st.form_submit_button("Save item"):
                st.success(f"Demo item {product or sku} validated. Connect a database to persist records.")

# ---------- Customers ----------
elif page == "Customers":
    header("Customer management","Understand customer value, segments and relationship health.","RELATIONSHIPS")
    a,b,c = st.columns(3)
    with a: kpi("TOTAL CUSTOMERS","1,284","↗ 5.4% this month")
    with b: kpi("REPEAT CUSTOMERS","68.2%","↗ 3.1% this month")
    with c: kpi("AVG. LIFETIME VALUE","₹26,400","↗ 6.7% this month")
    st.write("")
    segment = st.selectbox("Filter by segment",["All segments"]+sorted(customers["Segment"].unique().tolist()))
    view = customers if segment=="All segments" else customers[customers["Segment"]==segment]
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    panel_title("Customer directory","Customer engagement and lifetime value")
    st.dataframe(view,use_container_width=True,hide_index=True)
    st.markdown('</div>',unsafe_allow_html=True)
    st.write("")
    with st.expander("＋ Add customer"):
        with st.form("add_customer"):
            n = st.text_input("Customer / company name")
            email = st.text_input("Email address")
            seg = st.selectbox("Segment",["Retail","SMB","Enterprise"])
            if st.form_submit_button("Create customer"):
                st.success(f"Customer profile for {n or 'new customer'} is ready for database integration.")

# ---------- Logistics ----------
elif page == "Logistics":
    header("Logistics management","Track shipments, delivery performance and exceptions.","FULFILMENT")
    a,b,c = st.columns(3)
    with a: kpi("IN TRANSIT","38","Across 4 carrier partners")
    with b: kpi("ON-TIME DELIVERY","94.6%","↗ 1.8% this month")
    with c: kpi("DELIVERY EXCEPTIONS","3","Needs attention","#c47b19")
    st.write("")
    st.markdown('<div class="panel">',unsafe_allow_html=True)
    panel_title("Shipment tracker","Live tracking requires a carrier API connection")
    st.dataframe(shipments,use_container_width=True,hide_index=True)
    st.markdown('</div>',unsafe_allow_html=True)
    st.write("")
    st.markdown("#### Delivery workflow")
    st.progress(0.72,text="72% of today’s shipments delivered or out for delivery")
    with st.expander("＋ Create shipment"):
        with st.form("shipment"):
            order_id=st.text_input("Order ID")
            destination=st.text_input("Destination")
            carrier=st.selectbox("Carrier",["BlueDart","Delhivery","DTDC","India Post","Other"])
            if st.form_submit_button("Create shipment"):
                st.success(f"Shipment request for {order_id or 'new order'} prepared.")

# ---------- Analytics ----------
elif page == "Analytics":
    header("Business analytics","Explore performance trends and operational metrics.","INTELLIGENCE")
    metric = st.selectbox("Analyse metric",["Revenue","Orders","New customers"])
    series = {
        "Revenue": [10.2,11.8,11.1,14.4,15.9,18.4],
        "Orders": [142,158,151,184,213,248],
        "New customers": [74,81,79,102,118,136]
    }
    df = pd.DataFrame({"Month":["Jun","Jul","Aug","Sep","Oct","Nov"],metric:series[metric]})
    fig=px.bar(df,x="Month",y=metric,color=metric,color_continuous_scale=["#c9cdfa","#5967e8"])
    fig.update_layout(height=360,margin=dict(l=0,r=0,t=15,b=0),paper_bgcolor="white",plot_bgcolor="white",
                      coloraxis_showscale=False,font=dict(family="DM Sans",color="#738096"),
                      yaxis=dict(gridcolor="#edf0f5"),xaxis_title="")
    st.plotly_chart(fig,use_container_width=True)
    st.markdown("#### Performance snapshot")
    st.dataframe(pd.DataFrame({"Metric":["Revenue growth","Order growth","Customer growth","Fulfilment rate"],
                               "Current period":["+12.8%","+8.2%","+5.4%","96.8%"],
                               "Target":["+10.0%","+7.0%","+5.0%","95.0%"],
                               "Status":["Above target","Above target","Above target","Above target"]}),
                 use_container_width=True,hide_index=True)
    st.caption("Demo analytics are illustrative. Connect your operational database for accurate reporting.")

# ---------- AI Assistant ----------
elif page == "AI Assistant":
    header("AI assistant","Ask questions about the dashboard’s illustrative business data.","AI ASSISTANT")
    api_key = get_openai_api_key()
    if api_key:
        st.caption("Live mode: replies are generated by OpenAI using the illustrative dashboard data.")
    else:
        st.info("Local demo mode is ready. Ask about the sample dashboard data; add an OpenAI API key for live AI-generated replies.")

    if "ai_chat_history" not in st.session_state:
        st.session_state.ai_chat_history = [
            {"role": "assistant", "content": "Hi! I can help you explore the demo orders, inventory, customers, and shipments. What would you like to know?"}
        ]

    for message in st.session_state.ai_chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask about orders, inventory, customers, or shipments"):
        st.session_state.ai_chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        if not api_key:
            answer = demo_assistant_response(prompt)
            st.session_state.ai_chat_history.append({"role": "assistant", "content": answer})
            with st.chat_message("assistant"):
                st.markdown(answer)
        else:
            dashboard_context = f"""Illustrative dashboard KPIs:
- Revenue: ₹18.42 lakh; revenue growth: 12.8%
- Active orders: 248; order growth: 8.2%
- Customers: 1,284; customer growth: 5.4%
- Fulfilment rate: 96.8%

Demo orders:
{orders.to_string(index=False)}

Demo inventory:
{inventory.to_string(index=False)}

Demo customers:
{customers.to_string(index=False)}

Demo shipments:
{shipments.to_string(index=False)}"""
            system_message = {
                "role": "system",
                "content": (
                    "You are Nexus, a helpful business dashboard assistant. Answer questions using "
                    "only the dashboard context below. The figures and records are illustrative demo "
                    "data, not live business information. Be clear when the context does not contain "
                    "an answer; never invent facts or claim to have performed actions. You cannot "
                    "change records, place orders, or contact customers.\n\n"
                    f"{dashboard_context}"
                ),
            }
            api_messages = [system_message, *st.session_state.ai_chat_history[-20:]]
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            try:
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        answer = request_openai_chat(api_key, model, api_messages)
                    st.markdown(answer)
                st.session_state.ai_chat_history.append({"role": "assistant", "content": answer})
            except RuntimeError as error:
                st.error(str(error))

# ---------- AI Control Center ----------
elif page == "AI Control Center":
    header("AI agent control center","Configure, supervise and review your business automation agents.","AUTOMATION")
    agents = [
        ("Inventory Monitor","Checks stock thresholds and drafts replenishment tasks","Active","Every 30 min"),
        ("Order Coordinator","Routes new orders to fulfilment workflows","Active","On new order"),
        ("Customer Support","Classifies incoming queries and drafts replies","Paused","On new ticket"),
        ("Delivery Watch","Flags delayed shipments and prepares alerts","Active","Every 15 min"),
    ]
    for name,desc,status,trigger in agents:
        with st.container(border=True):
            x,y,z = st.columns([2.2,1,1])
            x.markdown(f"**{name}**  \n<small style='color:#738096'>{desc}</small>",unsafe_allow_html=True)
            y.markdown(f"**{status}**  \n<small style='color:#738096'>{trigger}</small>",unsafe_allow_html=True)
            if z.button("Configure",key=f"cfg_{name}"):
                st.session_state["selected_agent"]=name
    if st.session_state.get("selected_agent"):
        st.info(f"Selected agent: {st.session_state['selected_agent']}. Configure its tools, permissions, triggers and approval rules here.")
    st.write("")
    st.markdown("#### Agent activity")
    activity=pd.DataFrame({"Time":["11:32 AM","11:18 AM","10:54 AM","10:20 AM"],
                           "Agent":["Inventory Monitor","Order Coordinator","Delivery Watch","Customer Support"],
                           "Activity":["Low stock detected: Thermal Printer","Order ORD-1048 routed","Shipment TRK-88303 flagged delayed","Support response draft created"],
                           "Result":["Awaiting approval","Completed","Alert prepared","Awaiting review"]})
    st.dataframe(activity,use_container_width=True,hide_index=True)
    st.caption("Safety note: connect real agents with scoped permissions, audit logs and human approval for external actions.")

st.markdown("---")
st.markdown('<div style="display:flex;justify-content:space-between;flex-wrap:wrap;color:#8792a5;font-size:11px"><span>© 2026 NEXUS BUSINESS SYSTEMS</span><span>Secure workspace · Demo data</span></div>',unsafe_allow_html=True)
