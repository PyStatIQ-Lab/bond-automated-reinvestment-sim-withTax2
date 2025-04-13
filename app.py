import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from numpy_financial import pmt, ipmt, ppmt

# Set page config
st.set_page_config(page_title="Bond-Loan Investment Simulator", layout="wide")

# Custom styling
st.markdown("""
<style>
    .metric {font-size: 1.2rem !important;}
    .stSlider>div>div>div>div {background: #4f8bf9;}
    .stDataFrame {font-size: 14px;}
    .highlight {background-color: #fffacd; padding: 8px; border-radius: 5px;}
</style>
""", unsafe_allow_html=True)

# Title
st.title("💰 Bond-Loan Investment Simulator with Tax Calculation")

# Input parameters
with st.sidebar:
    st.header("Investment Parameters")
    initial = st.number_input("Investor Capital (₹)", 100000, 10000000, 100000, 10000)
    bond1_rate = st.slider("Bond 1 Interest Rate (% p.a.)", 1.0, 30.0, 14.0, 0.1)
    bond2_rate = st.slider("Bond 2 Expected Return (% p.a.)", 1.0, 30.0, 10.0, 0.1)
    loan_rate = st.slider("Loan Interest Rate (% p.a.)", 1.0, 20.0, 10.0, 0.1)
    months = st.slider("Tenure (Months)", 1, 60, 12, 1)
    
    st.header("Tax Parameters")
    investor_type = st.selectbox("Investor Type", ["Individual (30%)", "Private Ltd (25%)", "Custom Rate"])
    if investor_type == "Custom Rate":
        tax_rate = st.slider("Tax Rate (%)", 0.1, 35.0, 25.0, 0.1)
    else:
        tax_rate = 30.0 if "Individual" in investor_type else 25.0
    
    bond2_tax = st.slider("Bond 2 Tax Rate (%)", 0.0, 30.0, 15.0, 0.1)

# Calculations
# Bond 1 - Fixed Interest Bond
monthly_bond1_interest = initial * (bond1_rate / 12 / 100)

# Loan EMI Calculation
rate_per_period = loan_rate / 12 / 100
emi = -pmt(rate_per_period, months, initial)  # Using numpy_financial's pmt function

# Generate loan amortization schedule
loan_schedule = []
remaining_principal = initial
for month in range(1, months + 1):
    interest_payment = -ipmt(rate_per_period, month, months, initial)
    principal_payment = -ppmt(rate_per_period, month, months, initial)
    remaining_principal -= principal_payment
    loan_schedule.append({
        "Month": month,
        "EMI": emi,
        "Principal": principal_payment,
        "Interest": interest_payment,
        "Remaining Principal": remaining_principal
    })
loan_df = pd.DataFrame(loan_schedule)
total_loan_interest = loan_df["Interest"].sum()

# Bond 2 - Debt Mutual Fund with SIP
monthly_sip = monthly_bond1_interest  # Reinvest Bond 1 interest into Bond 2
initial_bond2 = initial  # Initial investment from loan

# Calculate Bond 2 returns (lump sum + SIP)
monthly_bond2_return = bond2_rate / 12 / 100

# Lump sum calculation
bond2_lumpsum = initial_bond2 * (1 + monthly_bond2_return)**months

# SIP calculation using future value formula
bond2_sip = monthly_sip * (((1 + monthly_bond2_return)**months - 1) / monthly_bond2_return) * (1 + monthly_bond2_return)

total_bond2_value = bond2_lumpsum + bond2_sip
bond2_gain = total_bond2_value - initial_bond2 - (monthly_sip * months)

# Tax Calculations
if "Individual" in investor_type:
    # For individuals
    bond1_tax = monthly_bond1_interest * months * (tax_rate / 100)
    bond2_tax_amount = bond2_gain * (bond2_tax / 100)
    total_tax = bond1_tax + bond2_tax_amount
    loan_interest_deduction = 0  # No deduction for personal loans
else:
    # For companies
    bond1_tax = monthly_bond1_interest * months * (tax_rate / 100)
    bond2_tax_amount = bond2_gain * (tax_rate / 100)  # Full business income tax
    loan_interest_deduction = total_loan_interest * (tax_rate / 100)
    total_tax = bond1_tax + bond2_tax_amount - loan_interest_deduction

# Final Returns
bond1_total_interest = monthly_bond1_interest * months
total_gain = bond1_total_interest + bond2_gain
net_gain = total_gain - total_loan_interest - total_tax
annualized_return = (net_gain / initial) * (12 / months) * 100

# Display results
st.subheader("💰 Investment Summary")
col1, col2, col3 = st.columns(3)
col1.metric("Bond 1 Total Interest", f"₹{bond1_total_interest:,.0f}", f"{bond1_rate}% p.a.")
col2.metric("Bond 2 Capital Gain", f"₹{bond2_gain:,.0f}", f"{bond2_rate}% p.a.")
col3.metric("Total Loan Interest Paid", f"₹{total_loan_interest:,.0f}", f"{loan_rate}% p.a.")

st.subheader("🧾 Tax Liability")
col1, col2, col3 = st.columns(3)
col1.metric("Bond 1 Tax", f"₹{bond1_tax:,.0f}", f"@{tax_rate}%")
col2.metric("Bond 2 Tax", f"₹{bond2_tax_amount:,.0f}", 
            f"@{bond2_tax}%" if "Individual" in investor_type else f"Business Income @{tax_rate}%")
if "Private" in investor_type:
    col3.metric("Loan Interest Deduction", f"₹{loan_interest_deduction:,.0f}", f"Tax saved @{tax_rate}%")

st.subheader("📊 Final Returns")
col1, col2, col3 = st.columns(3)
col1.metric("Total Gain Before Tax", f"₹{total_gain:,.0f}")
col2.metric("Total Tax Liability", f"₹{total_tax:,.0f}")
col3.metric("Net Profit After Tax", f"₹{net_gain:,.0f}", f"{annualized_return:.1f}% annualized")

# Loan Amortization Schedule
st.subheader("📅 Loan Amortization Schedule")
st.dataframe(loan_df.style.format({
    "Month": "{:.0f}",
    "EMI": "₹{:,.0f}",
    "Principal": "₹{:,.0f}",
    "Interest": "₹{:,.0f}",
    "Remaining Principal": "₹{:,.0f}"
}))

# Bond 2 Growth Projection
months_list = list(range(1, months + 1))
bond2_values = []
cumulative_investment = initial_bond2
for month in months_list:
    # Lump sum growth
    lump_sum = initial_bond2 * (1 + monthly_bond2_return)**month
    # SIP growth up to this month
    sip = monthly_sip * (((1 + monthly_bond2_return)**month - 1) / monthly_bond2_return) * (1 + monthly_bond2_return)
    bond2_values.append(lump_sum + sip)

fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(months_list, bond2_values, label="Bond 2 Portfolio Value", color='green')
ax.plot(months_list, loan_df["Remaining Principal"], label="Loan Outstanding", color='red', linestyle='--')
ax.set_title("Bond 2 Growth vs Loan Repayment")
ax.set_xlabel("Months")
ax.set_ylabel("Amount (₹)")
ax.legend()
ax.grid(True, alpha=0.3)
st.pyplot(fig)

# Calculation Methodology
with st.expander("🔍 Detailed Calculation Methodology"):
    st.markdown(f"""
    **Bond 1 (Fixed Interest Bond):**
    - Investment: ₹{initial:,.0f}
    - Monthly Interest: ₹{initial:,.0f} × ({bond1_rate}/12)% = ₹{monthly_bond1_interest:,.0f}
    - Total Interest (12 months): ₹{monthly_bond1_interest:,.0f} × {months} = ₹{bond1_total_interest:,.0f}
    - Tax: ₹{bond1_total_interest:,.0f} × {tax_rate}% = ₹{bond1_tax:,.0f}

    **Bond 2 (Debt Mutual Fund):**
    - Initial Investment: ₹{initial:,.0f} (from loan)
    - Monthly SIP: ₹{monthly_sip:,.0f} (Bond 1 interest)
    - Expected Return: {bond2_rate}% p.a.
    - After {months} months:
        - Lump sum growth: ₹{initial:,.0f} → ₹{bond2_lumpsum:,.0f}
        - SIP growth: ₹{monthly_sip:,.0f}/month → ₹{bond2_sip - (monthly_sip * months):,.0f} gain
    - Total Gain: ₹{bond2_gain:,.0f}
    - Tax: ₹{bond2_gain:,.0f} × {bond2_tax if 'Individual' in investor_type else tax_rate}% = ₹{bond2_tax_amount:,.0f}

    **Loan:**
    - Amount: ₹{initial:,.0f}
    - Interest Rate: {loan_rate}% p.a. (reducing balance)
    - EMI: ₹{emi:,.0f}
    - Total Interest Paid: ₹{total_loan_interest:,.0f}
    {"- Tax Deduction: ₹" + f"{loan_interest_deduction:,.0f}" + f" (@{tax_rate}%)" if "Private" in investor_type else ""}

    **Net Profit:**
    - Total Gains: ₹{bond1_total_interest:,.0f} (Bond 1) + ₹{bond2_gain:,.0f} (Bond 2) = ₹{total_gain:,.0f}
    - Less: Loan Interest ₹{total_loan_interest:,.0f}
    - Less: Taxes ₹{total_tax:,.0f}
    - Net Profit: ₹{net_gain:,.0f}
    - Annualized Return: {annualized_return:.1f}%
    """)

st.markdown("""
<div class="highlight">
<strong>💡 Key Assumptions:</strong>
1. Bond 1 interest is paid monthly and fully taxable
2. Bond 2 returns are calculated assuming constant {bond2_rate}% annual growth
3. Loan interest is calculated on reducing balance method
4. All Bond 1 interest is immediately reinvested in Bond 2
5. Taxes are calculated at year-end
</div>
""", unsafe_allow_html=True)
