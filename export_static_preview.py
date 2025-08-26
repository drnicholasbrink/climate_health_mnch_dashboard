"""
Export a static preview of the Dash app to index.html
- Computes default scenario values (global scope) to render key indicators
- Renders the 4 Plotly graphs used in the app
- Produces a single standalone HTML file (no Dash server required)
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

import plotly.graph_objects as go

# ----- Model inputs (copied from notebook) -----
mnch_outcomes = {
    'Gestational Diabetes': {'odds_ratio': 1.07, 'current_rate': 0.05, 'cost_per_case': 2000, 'ci_lower': 1.01, 'ci_upper': 1.54},
    'Hypertension during Pregnancy': {'odds_ratio': 1.12, 'current_rate': 0.1, 'cost_per_case': 1500, 'ci_lower': 1.03, 'ci_upper': 1.21},
    'Maternal Admission': {'odds_ratio': 1.01, 'current_rate': 0.02, 'cost_per_case': 1000, 'ci_lower': 1.00, 'ci_upper': 1.03},
    'Infections': {'odds_ratio': 1.29, 'current_rate': 0.02, 'cost_per_case': 800, 'ci_lower': 1.05, 'ci_upper': 1.58},
    'Prelabour Rupture of Membranes': {'odds_ratio': 1.08, 'current_rate': 0.02, 'cost_per_case': 1200, 'ci_lower': 1.07, 'ci_upper': 1.09},
    'Antenatal Bleeding': {'odds_ratio': 1.16, 'current_rate': 0.005, 'cost_per_case': 2500, 'ci_lower': 1.13, 'ci_upper': 1.40},
    'Cardiovascular Event': {'odds_ratio': 1.11, 'current_rate': 0.01, 'cost_per_case': 3000, 'ci_lower': 1.06, 'ci_upper': 1.15},
    'Stillbirth': {'odds_ratio': 1.14, 'current_rate': 0.005, 'cost_per_case': 5000, 'ci_lower': 0.99, 'ci_upper': 1.32},
    'Congenital Anomalies': {'odds_ratio': 1.13, 'current_rate': 0.02, 'cost_per_case': 10000, 'ci_lower': 0.99, 'ci_upper': 1.85},
    'Spontaneous Abortion': {'odds_ratio': 1.31, 'current_rate': 0.01, 'cost_per_case': 5000, 'ci_lower': 0.99, 'ci_upper': 3.30},
    'Non-reassuring Fetal Status': {'odds_ratio': 1.21, 'current_rate': 0.02, 'cost_per_case': 800, 'ci_lower': 1.12, 'ci_upper': 1.32},
    'Composite Outcome': {'odds_ratio': 1.42, 'current_rate': 0.1, 'cost_per_case': 2000, 'ci_lower': 1.00, 'ci_upper': 2.03},
    'Preterm Birth': {'odds_ratio': 1.04, 'current_rate': 0.1, 'cost_per_case': 32000, 'ci_lower': 1.03, 'ci_upper': 1.06},
    'Low Birth Weight': {'odds_ratio': 1.13, 'current_rate': 0.08, 'cost_per_case': 800, 'ci_lower': 1.02, 'ci_upper': 1.26},
    'Small for Gestational Age': {'odds_ratio': 1.10, 'current_rate': 0.02, 'cost_per_case': 800, 'ci_lower': 1.02, 'ci_upper': 1.18},
    'Neonatal Admission': {'odds_ratio': 1.22, 'current_rate': 0.02, 'cost_per_case': 1500, 'ci_lower': 1.02, 'ci_upper': 1.43},
    'Neonatal Morbidity': {'odds_ratio': 1.04, 'current_rate': 0.02, 'cost_per_case': 800, 'ci_lower': 1.03, 'ci_upper': 1.06},
    'Obstetric Complication': {'odds_ratio': 1.05, 'current_rate': 0.1, 'cost_per_case': 1500, 'ci_lower': 1.03, 'ci_upper': 1.06}
}

rcp_scenarios = {
    'RCP 2.6': 1.5,
    'RCP 4.5': 2.4,
    'RCP 6.0': 3.0,
    'RCP 8.5': 4.3
}

population_growth_rates = {
    'Low Growth': 0.01,
    'Medium Growth': 0.02,
    'High Growth': 0.03
}

pregnancy_growth_rates = {
    'High Reduction': -0.15,
    'Medium Reduction': -0.1,
    'Low Reduction': -0.05,
    'Low Growth': 0.01,
    'Medium Growth': 0.02,
    'High Growth': 0.03
}

# ----- Helpers (copied from notebook) -----
def calculate_population_growth(initial_population: float, growth_rate: float, num_years: int) -> List[float]:
    return [initial_population * ((1 + growth_rate) ** year) for year in range(num_years)]

def calculate_pregnancies(population: List[float], pregnancy_rate: float) -> List[float]:
    return [pop * pregnancy_rate for pop in population]

def calculate_temperature_increase_per_year(temp_increase_2100: float, start_year: int, end_year: int) -> List[float]:
    total_years = 2100 - 2024
    annual_increase = temp_increase_2100 / total_years
    return [annual_increase * (year - 2024) for year in range(start_year, end_year + 1)]

def calculate_additional_outcomes_and_costs(
    outcome: str,
    rcp_scenario: str,
    population_growth_curve: str,
    pregnancy_growth_curve: str,
    time_period: Tuple[int, int],
    current_population: float,
    initial_pregnancy_rate: float,
    adaptation_effectiveness: float,
):
    odds_ratio = mnch_outcomes[outcome]['odds_ratio']
    ci_lower = mnch_outcomes[outcome]['ci_lower']
    ci_upper = mnch_outcomes[outcome]['ci_upper']
    current_rate = mnch_outcomes[outcome]['current_rate']
    cost_per_case = mnch_outcomes[outcome]['cost_per_case']
    temp_increase_2100 = rcp_scenarios[rcp_scenario]
    population_growth_rate = population_growth_rates[population_growth_curve]
    pregnancy_growth_rate = pregnancy_growth_rates[pregnancy_growth_curve]

    start_year, end_year = time_period
    num_years = end_year - start_year + 1
    selected_years = list(range(start_year, end_year + 1))

    population_growth_selected = calculate_population_growth(current_population, population_growth_rate, num_years)
    pregnancies = calculate_pregnancies(population_growth_selected, initial_pregnancy_rate * (1 + pregnancy_growth_rate))
    baseline_outcomes = [preg * current_rate for preg in pregnancies]

    temperature_increase_per_year = calculate_temperature_increase_per_year(temp_increase_2100, start_year, end_year)
    projected_rates = [current_rate * (odds_ratio ** temp_increase) for temp_increase in temperature_increase_per_year]
    projected_outcomes = [rate * preg for rate, preg in zip(projected_rates, pregnancies)]

    additional_outcomes = [proj - base for proj, base in zip(projected_outcomes, baseline_outcomes)]
    effective_additional_outcomes = [o * (1 - adaptation_effectiveness / 100) for o in additional_outcomes]
    effective_additional_outcomes_lower = [o * (1 - adaptation_effectiveness / 100) * ci_lower / odds_ratio for o in additional_outcomes]
    effective_additional_outcomes_upper = [o * (1 - adaptation_effectiveness / 100) * ci_upper / odds_ratio for o in additional_outcomes]

    costs = [o * cost_per_case for o in effective_additional_outcomes]
    costs_lower = [o * cost_per_case for o in effective_additional_outcomes_lower]
    costs_upper = [o * cost_per_case for o in effective_additional_outcomes_upper]

    return selected_years, effective_additional_outcomes, costs, additional_outcomes, effective_additional_outcomes_lower, effective_additional_outcomes_upper, costs_lower, costs_upper

def calculate_attributable_fraction(odds_ratio: float) -> float:
    return (odds_ratio - 1) / odds_ratio

# ----- Defaults matching the app -----
DEFAULTS = dict(
    outcome='Preterm Birth',
    rcp_scenario='RCP 2.6',
    population_growth_curve='Medium Growth',
    pregnancy_growth_curve='Medium Growth',
    time_period=(2024, 2030),
    current_population=7_000_000_000,  # Global default
    initial_pregnancy_rate=0.02,
    adaptation_effectiveness=50,
)

# ----- Compute preview -----
sy, eff_add_outcomes, costs, add_outcomes, eff_low, eff_up, cost_low, cost_up = calculate_additional_outcomes_and_costs(
    DEFAULTS['outcome'],
    DEFAULTS['rcp_scenario'],
    DEFAULTS['population_growth_curve'],
    DEFAULTS['pregnancy_growth_curve'],
    DEFAULTS['time_period'],
    DEFAULTS['current_population'],
    DEFAULTS['initial_pregnancy_rate'],
    DEFAULTS['adaptation_effectiveness'],
)

# Worst/zero adaptation series for savings and prevented
_, worst_eff_add, worst_costs, worst_add, _, _, _, _ = calculate_additional_outcomes_and_costs(
    DEFAULTS['outcome'], 'RCP 8.5', DEFAULTS['population_growth_curve'], DEFAULTS['pregnancy_growth_curve'], DEFAULTS['time_period'], DEFAULTS['current_population'], DEFAULTS['initial_pregnancy_rate'], 0
)
_, zero_adapt_outcomes, zero_adapt_costs, _, _, _, _, _ = calculate_additional_outcomes_and_costs(
    DEFAULTS['outcome'], DEFAULTS['rcp_scenario'], DEFAULTS['population_growth_curve'], DEFAULTS['pregnancy_growth_curve'], DEFAULTS['time_period'], DEFAULTS['current_population'], DEFAULTS['initial_pregnancy_rate'], 0
)

mitigation_savings = [w - c for w, c in zip(worst_costs, costs)]
adaptation_savings = [z - c for z, c in zip(zero_adapt_costs, costs)]
mitigation_prevented = [w - s for w, s in zip(worst_add, eff_add_outcomes)]
adaptation_prevented = [z - s for z, s in zip(zero_adapt_outcomes, eff_add_outcomes)]

# Indicators
odds_ratio = mnch_outcomes[DEFAULTS['outcome']]['odds_ratio']
current_rate = mnch_outcomes[DEFAULTS['outcome']]['current_rate']
attrib_frac = calculate_attributable_fraction(odds_ratio)

total_additional_outcomes = int(round(sum(eff_add_outcomes)))
_total_cost = round(sum(costs), 2)
_total_mitigation_savings = round(sum(mitigation_savings), 2)
_total_adaptation_savings = round(sum(adaptation_savings), 2)
_total_mitigation_prevented = int(round(sum(mitigation_prevented)))
_total_adaptation_prevented = int(round(sum(adaptation_prevented)))

# ----- Figures (matching the app styles) -----
graph_config = dict(
    font=dict(family='-apple-system, BlinkMacSystemFont, SF Pro Display, sans-serif', size=14),
    plot_bgcolor='#FAFAFA',
    paper_bgcolor='#FFFFFF',
    colorway=['#007AFF', '#FF3B30', '#30D158', '#FF9500', '#AF52DE', '#FF2D92', '#5856D6', '#32D74B'],
)

# Outcomes with CI and temperature on y2
fig_outcomes = go.Figure()
fig_outcomes.add_trace(go.Scatter(x=sy, y=eff_add_outcomes, mode='lines+markers', name=f"Selected Scenario ({DEFAULTS['rcp_scenario']}, {DEFAULTS['adaptation_effectiveness']}%)", line=dict(color='#007AFF', width=3), marker=dict(size=6, color='#007AFF')))
fig_outcomes.add_trace(go.Scatter(x=sy + sy[::-1], y=eff_up + eff_low[::-1], fill='toself', fillcolor='rgba(0, 122, 255, 0.1)', line=dict(color='rgba(255, 255, 255, 0)'), showlegend=False, name='Confidence Interval'))

temp_series = calculate_temperature_increase_per_year(rcp_scenarios[DEFAULTS['rcp_scenario']], DEFAULTS['time_period'][0], DEFAULTS['time_period'][1])
fig_outcomes.add_trace(go.Scatter(x=sy, y=temp_series, mode='lines+markers', name='Temperature Increase', yaxis='y2', line=dict(color='#FF3B30', width=3), marker=dict(size=6, color='#FF3B30')))
fig_outcomes.update_layout(title=dict(text=f"Climate Impact on {DEFAULTS['outcome']} Cases ({sy[0]}-{sy[-1]})", font=dict(size=18, family='-apple-system, BlinkMacSystemFont, SF Pro Display, sans-serif'), x=0.5), xaxis_title='Year', yaxis=dict(title='Additional Health Cases', tickfont=dict(color="#007AFF")), yaxis2=dict(title='Temperature Increase (°C)', tickfont=dict(color="#FF3B30"), overlaying='y', side='right'), **graph_config, legend=dict(yanchor='top', y=0.99, xanchor='left', x=0.01, bgcolor='rgba(255,255,255,0.8)'))

# Prevention impact
fig_prevent = go.Figure()
fig_prevent.add_trace(go.Scatter(x=sy, y=worst_add, mode='lines+markers', name='Worst Case (RCP 8.5, 0% Adaptation)', line=dict(color='#FF3B30', width=3), marker=dict(size=6, color='#FF3B30')))
fig_prevent.add_trace(go.Scatter(x=sy, y=eff_add_outcomes, mode='lines+markers', name=f"Selected Scenario ({DEFAULTS['rcp_scenario']}, {DEFAULTS['adaptation_effectiveness']}%)", line=dict(color='#007AFF', width=3), marker=dict(size=6, color='#007AFF')))
fig_prevent.add_trace(go.Scatter(x=sy + sy[::-1], y=worst_add + eff_add_outcomes[::-1], fill='toself', fillcolor='rgba(48, 209, 88, 0.2)', line=dict(color='rgba(255, 255, 255, 0)'), showlegend=True, name='Mitigation Benefit'))
fig_prevent.add_trace(go.Scatter(x=sy + sy[::-1], y=zero_adapt_outcomes + eff_add_outcomes[::-1], fill='toself', fillcolor='rgba(0, 122, 255, 0.2)', line=dict(color='rgba(255, 255, 255, 0)'), showlegend=True, name='Adaptation Benefit'))
fig_prevent.update_layout(title=dict(text=f"Prevention Impact: Cases Avoided ({sy[0]}-{sy[-1]})", font=dict(size=18, family='-apple-system, BlinkMacSystemFont, SF Pro Display, sans-serif'), x=0.5), xaxis_title='Year', yaxis_title='Additional Health Cases', **graph_config, legend=dict(yanchor='top', y=0.99, xanchor='left', x=0.01, bgcolor='rgba(255,255,255,0.8)'))

# Costs with CI
fig_costs = go.Figure()
fig_costs.add_trace(go.Scatter(x=sy, y=costs, mode='lines+markers', name=f"Selected Scenario ({DEFAULTS['rcp_scenario']}, {DEFAULTS['adaptation_effectiveness']}%)", line=dict(color='#007AFF', width=3), marker=dict(size=6, color='#007AFF')))
fig_costs.add_trace(go.Scatter(x=sy + sy[::-1], y=cost_up + cost_low[::-1], fill='toself', fillcolor='rgba(0, 122, 255, 0.1)', line=dict(color='rgba(255, 255, 255, 0)'), showlegend=False, name='Cost Range'))
fig_costs.update_layout(title=dict(text=f"Economic Impact: Healthcare Costs ({sy[0]}-{sy[-1]})", font=dict(size=18, family='-apple-system, BlinkMacSystemFont, SF Pro Display, sans-serif'), x=0.5), xaxis_title='Year', yaxis_title='Healthcare Costs (USD)', **graph_config, legend=dict(yanchor='top', y=0.99, xanchor='left', x=0.01, bgcolor='rgba(255,255,255,0.8)'))

# Cost savings
fig_savings = go.Figure()
fig_savings.add_trace(go.Scatter(x=sy, y=worst_costs, mode='lines+markers', name='Worst Case (RCP 8.5, 0% Adaptation)', line=dict(color='#FF3B30', width=3), marker=dict(size=6, color='#FF3B30')))
fig_savings.add_trace(go.Scatter(x=sy, y=costs, mode='lines+markers', name=f"Selected Scenario ({DEFAULTS['rcp_scenario']}, {DEFAULTS['adaptation_effectiveness']}%)", line=dict(color='#007AFF', width=3), marker=dict(size=6, color='#007AFF')))
fig_savings.add_trace(go.Scatter(x=sy + sy[::-1], y=worst_costs + costs[::-1], fill='toself', fillcolor='rgba(48, 209, 88, 0.2)', line=dict(color='rgba(255, 255, 255, 0)'), showlegend=True, name='Mitigation Savings'))
fig_savings.add_trace(go.Scatter(x=sy + sy[::-1], y=zero_adapt_costs + costs[::-1], fill='toself', fillcolor='rgba(0, 122, 255, 0.2)', line=dict(color='rgba(255, 255, 255, 0)'), showlegend=True, name='Adaptation Savings'))
fig_savings.update_layout(title=dict(text=f"Economic Benefits: Cost Savings Analysis ({sy[0]}-{sy[-1]})", font=dict(size=18, family='-apple-system, BlinkMacSystemFont, SF Pro Display, sans-serif'), x=0.5), xaxis_title='Year', yaxis_title='Healthcare Costs (USD)', **graph_config, legend=dict(yanchor='top', y=0.99, xanchor='left', x=0.01, bgcolor='rgba(255,255,255,0.8)'))

# HTML building
base_css = """
:root { --bg: #0f172a; --text: #e5e7eb; --muted: #94a3b8; }
* { box-sizing: border-box; }
html, body { height:100%; margin:0; }
body { background: radial-gradient(1200px 600px at 10% -10%, #172554 0%, rgba(2,6,23,0) 60%), linear-gradient(180deg, #020617 0%, #0b1220 100%); color: var(--text); font-family: -apple-system,BlinkMacSystemFont,Inter,Segoe UI,Roboto,Helvetica,Arial,sans-serif; }
.wrap { max-width: 1280px; margin: 0 auto; padding: 32px 20px 56px; }
header { text-align:center; margin-bottom: 28px; }
header h1 { font-size: clamp(24px, 5vw, 36px); margin: 0; letter-spacing: -0.02em; }
header p { color: var(--muted); margin: 6px 0 0; }
.grid { display:grid; gap:16px; }
.card { background: rgba(17, 24, 39, 0.6); border: 1px solid rgba(148,163,184,0.12); border-radius: 16px; padding: 16px; box-shadow: 0 10px 30px rgba(2,6,23,0.35), inset 0 1px 0 rgba(255,255,255,0.04); }
.featured { display:grid; grid-template-columns: repeat(4, minmax(160px,1fr)); gap: 16px; }
.featured .indicator { background: rgba(2,6,23,0.5); border: 1px solid rgba(148,163,184,0.12); border-radius: 12px; padding: 16px; text-align:center; }
.featured .indicator h4 { margin: 0 0 6px; color: var(--muted); font-weight: 600; font-size: 12px; text-transform: none; letter-spacing: 0.3px; }
.featured .indicator .value { font-size: clamp(18px, 3vw, 28px); font-weight: 700; }
.graphs { display:grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 16px; }
.plot { background: rgba(2,6,23,0.5); border: 1px solid rgba(148,163,184,0.12); border-radius: 12px; padding: 8px; }
small { color: var(--muted); }
"""

figs_html = "\n".join([
    fig_outcomes.to_html(full_html=False, include_plotlyjs=False),
    fig_prevent.to_html(full_html=False, include_plotlyjs=False),
    fig_costs.to_html(full_html=False, include_plotlyjs=False),
    fig_savings.to_html(full_html=False, include_plotlyjs=False),
])

html = f"""<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Climate Health Impact Dashboard — Static Preview</title>
    <meta name=\"description\" content=\"Static snapshot of the dashboard (no server)\" />
    <script src=\"https://cdn.plot.ly/plotly-2.27.1.min.js\"></script>
    <style>{base_css}</style>
  </head>
  <body>
    <div class=\"wrap\">
      <header>
        <h1>Climate Health Impact Dashboard</h1>
        <p>Static preview (defaults shown; interactive controls not included)</p>
        <small>Outcome: {DEFAULTS['outcome']} • Scenario: {DEFAULTS['rcp_scenario']} • Pop growth: {DEFAULTS['population_growth_curve']} • Pregnancy trend: {DEFAULTS['pregnancy_growth_curve']} • Years: {sy[0]}–{sy[-1]} • Adaptation: {DEFAULTS['adaptation_effectiveness']}%</small>
      </header>

      <section class=\"card\">
        <div class=\"featured\">
          <div class=\"indicator\"><h4>Additional Cases</h4><div class=\"value\">{total_additional_outcomes:,}</div></div>
          <div class=\"indicator\"><h4>Total Cost</h4><div class=\"value\">${_total_cost:,.2f}</div></div>
          <div class=\"indicator\"><h4>Mitigation Savings</h4><div class=\"value\">${_total_mitigation_savings:,.2f}</div></div>
          <div class=\"indicator\"><h4>Adaptation Savings</h4><div class=\"value\">${_total_adaptation_savings:,.2f}</div></div>
        </div>
      </section>

      <section class=\"grid\">
        <div class=\"card\">
          <div class=\"graphs\">
            <div class=\"plot\">{figs_html}</div>
          </div>
        </div>
      </section>

      <section class=\"grid\">
        <div class=\"card\">
          <small>Note: This file is static. To interact with controls, run the Dash app from the notebook and visit http://127.0.0.1:8050/</small>
        </div>
      </section>
    </div>
  </body>
</html>
"""

# Write to project root index.html
out_path = Path(__file__).resolve().parent / "index.html"
out_path.write_text(html, encoding="utf-8")
print(f"Wrote static preview to {out_path}")
