"""
Interactive Dashboard for FDR Analysis - López de Prado Framework

This Dash application provides an interactive visualization of the False Discovery Rate
analysis with search and selection effects as described in López de Prado's paper.

Features:
- Interactive parameter exploration (K, π₀, δ₁, threshold)
- Dynamic distribution plots with annotated rejection regions
- Error rate decomposition and FDR evolution
- Sensitivity analysis and scenario comparison
- Export capabilities for publication-quality figures

Usage:
    python fdR_dashboard.py
    
Then open http://127.0.0.1:8050 in your browser.
"""

import numpy as np
import pandas as pd
from scipy.stats import norm
from scipy.special import ndtr
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from dash import Dash, html, dcc, Input, Output, State
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# CORE MATHEMATICAL FUNCTIONS
# ============================================================

def logistic(a):
    """Map R to (0,1)."""
    return 1.0 / (1.0 + np.exp(-a))

def inverse_logistic(p):
    """Map (0,1) to R."""
    return np.log(p / (1.0 - p))

def cdf_mixture(x, pi0, delta1, sigma0, sigma1):
    """
    CDF of the base mixture distribution.
    
    F(x) = π₀·Φ(x/σ₀) + (1-π₀)·Φ((x-δ₁)/σ₁)
    """
    z0 = x / sigma0
    z1 = (x - delta1) / sigma1
    F0 = ndtr(z0)
    F1 = ndtr(z1)
    return pi0 * F0 + (1.0 - pi0) * F1

def pdf_mixture(x, pi0, delta1, sigma0, sigma1):
    """
    PDF of the base mixture distribution.
    
    f(x) = π₀·φ(x/σ₀)/σ₀ + (1-π₀)·φ((x-δ₁)/σ₁)/σ₁
    """
    z0 = x / sigma0
    z1 = (x - delta1) / sigma1
    f0 = np.exp(-0.5 * z0**2) / np.sqrt(2.0 * np.pi) / sigma0
    f1 = np.exp(-0.5 * z1**2) / np.sqrt(2.0 * np.pi) / sigma1
    return pi0 * f0 + (1.0 - pi0) * f1

def cdf_selected_maximum(x, pi0, delta1, sigma0, sigma1, K):
    """
    CDF of the selected maximum statistic.
    
    F_Θ,K(x) = [F_mixture(x)]^K
    """
    base_cdf = cdf_mixture(x, pi0, delta1, sigma0, sigma1)
    return base_cdf ** K

def pdf_selected_maximum(x, pi0, delta1, sigma0, sigma1, K):
    """
    PDF of the selected maximum statistic.
    
    f_Θ,K(x) = K·[F_mixture(x)]^(K-1) · f_mixture(x)
    """
    base_cdf = cdf_mixture(x, pi0, delta1, sigma0, sigma1)
    base_pdf = pdf_mixture(x, pi0, delta1, sigma0, sigma1)
    return K * (base_cdf ** (K - 1)) * base_pdf

def compute_error_rates(pi0, delta1, sigma0, sigma1, K, c):
    """
    Compute familywise Type I and Type II error rates.
    
    Parameters:
    -----------
    pi0 : float
        Null prevalence
    delta1 : float
        Alternative mean shift
    sigma0 : float
        Null scale parameter
    sigma1 : float
        Alternative scale parameter  
    K : int
        Search intensity (number of trials)
    c : float
        Rejection threshold
    
    Returns:
    --------
    dict with alpha_K, beta_K, fdr, power
    """
    # Primitive error rates
    alpha = 1.0 - ndtr(c / sigma0)
    beta = ndtr((c - delta1) / sigma1)
    
    # Familywise Type I error: P(reject | all null)
    alpha_K = 1.0 - (1.0 - alpha) ** K
    
    # Familywise Type II error: P(not reject | at least one non-null)
    if pi0 < 1.0:
        term1 = (pi0 * (1.0 - alpha) + (1.0 - pi0) * beta) ** K
        term2 = (pi0 * (1.0 - alpha)) ** K
        beta_K = (term1 - term2) / (1.0 - pi0 ** K)
    else:
        beta_K = beta ** K
    
    # Power
    power = 1.0 - beta_K
    
    # False Discovery Rate
    if alpha_K * pi0 + power * (1.0 - pi0) > 0:
        fdr = (alpha_K * pi0) / (alpha_K * pi0 + power * (1.0 - pi0))
    else:
        fdr = 0.0
    
    return {
        'alpha': alpha,
        'beta': beta,
        'alpha_K': alpha_K,
        'beta_K': beta_K,
        'power': power,
        'fdr': fdr
    }

def generate_table1_data(pi0_A=0.75, pi0_B=0.10, SR1=0.30, K=5, c=1.96):
    """Generate data for Table 1 replication (identification failure example)."""
    x_grid = np.arange(2.00, 4.01, 0.25)
    
    results = []
    for x in x_grid:
        # Case A: Search and selection
        tail_A = 1.0 - cdf_selected_maximum(x, pi0_A, SR1, 1.0, 1.0, K)
        tail_A_c = 1.0 - cdf_selected_maximum(c, pi0_A, SR1, 1.0, 1.0, K)
        cond_A = tail_A / tail_A_c
        
        # Case B: No search
        tail_B = 1.0 - cdf_mixture(x, pi0_B, SR1, 1.0, 1.0)
        tail_B_c = 1.0 - cdf_mixture(c, pi0_B, SR1, 1.0, 1.0)
        cond_B = tail_B / tail_B_c
        
        results.append({
            'x': x,
            'Case_A': cond_A,
            'Case_B': cond_B,
            'Difference': abs(cond_A - cond_B)
        })
    
    return pd.DataFrame(results)

# ============================================================
# PLOTTING FUNCTIONS
# ============================================================

def create_distribution_plot(pi0, delta1, sigma0, sigma1, K, c):
    """Create interactive distribution plot with null, alternative, and selected maximum."""
    
    x = np.linspace(-0.5, 4.0, 500)
    
    # Base distributions
    null_pdf = norm.pdf(x, 0, sigma0)
    alt_pdf = norm.pdf(x, delta1, sigma1)
    mixture_pdf = pdf_mixture(x, pi0, delta1, sigma0, sigma1)
    selected_pdf = pdf_selected_maximum(x, pi0, delta1, sigma0, sigma1, K)
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Probability Density Functions', 'Cumulative Distribution Functions'),
        vertical_spacing=0.12
    )
    
    # PDF subplot
    fig.add_trace(go.Scatter(
        x=x, y=null_pdf, name='Null (H₀)', mode='lines',
        line=dict(color='blue', width=2), opacity=0.8
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=x, y=alt_pdf, name='Alternative (H₁)', mode='lines',
        line=dict(color='green', width=2, dash='dash'), opacity=0.8
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=x, y=mixture_pdf, name='Mixture', mode='lines',
        line=dict(color='orange', width=2), opacity=0.8
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=x, y=selected_pdf, name=f'Selected Max (K={K})', mode='lines',
        line=dict(color='red', width=3), opacity=1.0
    ), row=1, col=1)
    
    # Add threshold line
    fig.add_shape(type='line',
        x0=c, x1=c, y0=0, y1=max(selected_pdf),
        line=dict(color='black', width=2, dash='dot'),
        name='Threshold c', row=1, col=1
    )
    
    # Shade rejection region
    x_reject = x[x >= c]
    y_reject = selected_pdf[x >= c]
    fig.add_trace(go.Scatter(
        x=np.concatenate([x_reject, x_reject[::-1]]),
        y=np.concatenate([y_reject, np.zeros_like(x_reject)]),
        fill='toself', fillcolor='rgba(255,0,0,0.2)',
        line=dict(color='rgba(255,0,0,0)'),
        name='Rejection Region', showlegend=True
    ), row=1, col=1)
    
    # CDF subplot
    null_cdf = norm.cdf(x, 0, sigma0)
    alt_cdf = norm.cdf(x, delta1, sigma1)
    mixture_cdf = cdf_mixture(x, pi0, delta1, sigma0, sigma1)
    selected_cdf = cdf_selected_maximum(x, pi0, delta1, sigma0, sigma1, K)
    
    fig.add_trace(go.Scatter(
        x=x, y=null_cdf, name='Null (H₀)', mode='lines',
        line=dict(color='blue', width=2), opacity=0.8, showlegend=False
    ), row=2, col=1)
    
    fig.add_trace(go.Scatter(
        x=x, y=alt_cdf, name='Alternative (H₁)', mode='lines',
        line=dict(color='green', width=2, dash='dash'), opacity=0.8, showlegend=False
    ), row=2, col=1)
    
    fig.add_trace(go.Scatter(
        x=x, y=mixture_cdf, name='Mixture', mode='lines',
        line=dict(color='orange', width=2), opacity=0.8, showlegend=False
    ), row=2, col=1)
    
    fig.add_trace(go.Scatter(
        x=x, y=selected_cdf, name=f'Selected Max (K={K})', mode='lines',
        line=dict(color='red', width=3), opacity=1.0, showlegend=False
    ), row=2, col=1)
    
    # Update layout
    fig.update_layout(
        height=700,
        title_text='<b>Distribution Analysis: Search and Selection Effects</b>',
        title_x=0.5,
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    fig.update_xaxes(title_text='Sharpe Ratio', row=1, col=1)
    fig.update_xaxes(title_text='Sharpe Ratio', row=2, col=1)
    fig.update_yaxes(title_text='Density', row=1, col=1)
    fig.update_yaxes(title_text='Probability', row=2, col=1)
    
    return fig

def create_fdr_evolution_plot(pi0, delta1, sigma0, sigma1, c):
    """Create FDR evolution plot as function of K."""
    
    K_values = np.arange(1, 51, 1)
    fdr_values = []
    alpha_K_values = []
    beta_K_values = []
    
    for K in K_values:
        errors = compute_error_rates(pi0, delta1, sigma0, sigma1, K, c)
        fdr_values.append(errors['fdr'])
        alpha_K_values.append(errors['alpha_K'])
        beta_K_values.append(errors['beta_K'])
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('False Discovery Rate vs Search Intensity', 'Error Rate Decomposition'),
        vertical_spacing=0.12
    )
    
    # FDR plot
    fig.add_trace(go.Scatter(
        x=K_values, y=fdr_values, name='FDR', mode='lines+markers',
        line=dict(color='red', width=3), marker=dict(size=6),
        fill='tozeroy', fillcolor='rgba(255,0,0,0.1)'
    ), row=1, col=1)
    
    # Add horizontal lines for literature estimates
    fig.add_hline(y=0.05, line=dict(color='blue', width=1, dash='dash'), 
                  annotation_text='Literature FDR (5%)', row=1, col=1)
    fig.add_hline(y=0.15, line=dict(color='blue', width=1, dash='dash'),
                  annotation_text='Literature FDR (15%)', row=1, col=1)
    
    # Error rate decomposition
    fig.add_trace(go.Scatter(
        x=K_values, y=alpha_K_values, name='Type I Error (α_K)', mode='lines',
        line=dict(color='orange', width=2)
    ), row=2, col=1)
    
    fig.add_trace(go.Scatter(
        x=K_values, y=beta_K_values, name='Type II Error (β_K)', mode='lines',
        line=dict(color='green', width=2)
    ), row=2, col=1)
    
    fig.update_layout(
        height=600,
        title_text='<b>FDR Evolution with Search Intensity</b>',
        title_x=0.5,
        hovermode='x unified'
    )
    
    fig.update_xaxes(title_text='Search Intensity (K)', row=2, col=1)
    fig.update_yaxes(title_text='FDR', range=[0, 1], row=1, col=1)
    fig.update_yaxes(title_text='Error Rate', range=[0, 1], row=2, col=1)
    
    # Add annotations
    fig.add_annotation(
        x=5, y=fdr_values[4], text=f'FDR at K=5: {fdr_values[4]:.1%}',
        showarrow=True, arrowhead=2, ax=0, ay=-40,
        bgcolor='white', bordercolor='red'
    )
    
    return fig

def create_sensitivity_heatmap(delta1, sigma0, sigma1, c):
    """Create FDR heatmap as function of K and π₀."""
    
    K_range = np.arange(1, 31, 1)
    pi0_range = np.arange(0.1, 1.0, 0.05)
    
    fdr_matrix = np.zeros((len(pi0_range), len(K_range)))
    
    for i, pi0 in enumerate(pi0_range):
        for j, K in enumerate(K_range):
            errors = compute_error_rates(pi0, delta1, sigma0, sigma1, K, c)
            fdr_matrix[i, j] = errors['fdr']
    
    fig = go.Figure(data=go.Heatmap(
        z=fdr_matrix,
        x=K_range,
        y=[f'{p:.2f}' for p in pi0_range],
        colorscale='RdYlBu_r',
        colorbar=dict(title='FDR'),
        hovertemplate='K=%{x}<br>π₀=%{y}<br>FDR=%{z:.2%}<extra></extra>'
    ))
    
    fig.update_layout(
        title='<b>Sensitivity Analysis: FDR as Function of K and π₀</b>',
        title_x=0.5,
        xaxis_title='Search Intensity (K)',
        yaxis_title='Null Prevalence (π₀)',
        height=500
    )
    
    return fig

def create_identification_failure_plot():
    """Replicate Table 1 identification failure example."""
    
    df = generate_table1_data()
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['x'], y=df['Case_A'], name='Case A (Search, K=5, π₀=0.75)',
        mode='lines+markers', line=dict(color='red', width=3), marker=dict(size=8)
    ))
    
    fig.add_trace(go.Scatter(
        x=df['x'], y=df['Case_B'], name='Case B (No Search, K=1, π₀=0.10)',
        mode='lines+markers', line=dict(color='blue', width=3, dash='dash'), marker=dict(size=8)
    ))
    
    fig.add_trace(go.Scatter(
        x=df['x'], y=df['Difference'], name='Absolute Difference',
        mode='lines', line=dict(color='gray', width=2, dash='dot')
    ))
    
    fig.update_layout(
        title='<b>Identification Failure: Observation Equivalence</b><br><sup>Two different DGP produce nearly identical conditional tail probabilities</sup>',
        title_x=0.5,
        xaxis_title='Threshold x',
        yaxis_title='P(X ≥ x | X ≥ 1.96)',
        height=500,
        hovermode='x unified'
    )
    
    # Add annotation
    fig.add_annotation(
        x=3.0, y=0.35,
        text='Max difference: {:.3f}'.format(df['Difference'].max()),
        showarrow=False, bgcolor='white', bordercolor='black'
    )
    
    return fig

def create_metrics_cards(pi0, delta1, sigma0, sigma1, K, c):
    """Create metrics cards for key statistics."""
    
    errors = compute_error_rates(pi0, delta1, sigma0, sigma1, K, c)
    
    cards = html.Div([
        html.Div([
            html.H3(f"{errors['fdr']:.1%}", style={'color': '#d62728', 'margin': '0'}),
            html.P('False Discovery Rate', style={'margin': '0', 'fontSize': '14px'})
        ], style={'padding': '20px', 'textAlign': 'center', 'backgroundColor': '#f7f7f7', 
                  'borderRadius': '5px', 'flex': '1', 'margin': '5px'}),
        
        html.Div([
            html.H3(f"{errors['alpha_K']:.1%}", style={'color': '#ff7f0e', 'margin': '0'}),
            html.P('Familywise Type I Error', style={'margin': '0', 'fontSize': '14px'})
        ], style={'padding': '20px', 'textAlign': 'center', 'backgroundColor': '#f7f7f7',
                  'borderRadius': '5px', 'flex': '1', 'margin': '5px'}),
        
        html.Div([
            html.H3(f"{errors['beta_K']:.1%}", style={'color': '#2ca02c', 'margin': '0'}),
            html.P('Familywise Type II Error', style={'margin': '0', 'fontSize': '14px'})
        ], style={'padding': '20px', 'textAlign': 'center', 'backgroundColor': '#f7f7f7',
                  'borderRadius': '5px', 'flex': '1', 'margin': '5px'}),
        
        html.Div([
            html.H3(f"{errors['power']:.1%}", style={'color': '#1f77b4', 'margin': '0'}),
            html.P('Power (1-β_K)', style={'margin': '0', 'fontSize': '14px'})
        ], style={'padding': '20px', 'textAlign': 'center', 'backgroundColor': '#f7f7f7',
                  'borderRadius': '5px', 'flex': '1', 'margin': '5px'}),
    ], style={'display': 'flex', 'justifyContent': 'space-around', 'marginBottom': '20px'})
    
    return cards

# ============================================================
# DASH APPLICATION
# ============================================================

app = Dash(__name__, suppress_callback_exceptions=True)
app.title = "FDR Analysis Dashboard - López de Prado Framework"

app.layout = html.Div([
    # Header
    html.Div([
        html.H1("🔍 False Discovery Rate in Finance", 
                style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '5px'}),
        html.H3("Search and Selection Model - López de Prado Framework",
                style={'textAlign': 'center', 'color': '#7f8c8d', 'marginTop': '0'}),
        html.P("Interactive exploration of how latent search and selection dramatically increases FDR estimates",
               style={'textAlign': 'center', 'color': '#95a5a6', 'fontStyle': 'italic'})
    ], style={'padding': '20px', 'backgroundColor': '#ecf0f1', 'borderBottom': '3px solid #3498db'}),
    
    # Control Panel
    html.Div([
        html.H4("⚙️ Parameter Controls", style={'color': '#2c3e50', 'marginTop': '0'}),
        
        html.Div([
            html.Div([
                html.Label("Search Intensity (K)", style={'fontWeight': 'bold'}),
                dcc.Slider(
                    id='k-slider',
                    min=1, max=50, step=1, value=5,
                    marks={i: str(i) for i in [1, 5, 10, 20, 30, 40, 50]},
                    tooltip={'placement': 'top', 'always_visible': True}
                ),
                html.P("Number of candidate specifications tested", 
                       style={'fontSize': '12px', 'color': '#7f8c8d'})
            ], style={'width': '48%', 'display': 'inline-block', 'padding': '10px'}),
            
            html.Div([
                html.Label("Null Prevalence (π₀)", style={'fontWeight': 'bold'}),
                dcc.Slider(
                    id='pi0-slider',
                    min=0.0, max=1.0, step=0.01, value=0.75,
                    marks={i/10: f'{i/10:.1f}' for i in range(0, 11)},
                    tooltip={'placement': 'top', 'always_visible': True}
                ),
                html.P("Proportion of strategies with no true effect",
                       style={'fontSize': '12px', 'color': '#7f8c8d'})
            ], style={'width': '48%', 'display': 'inline-block', 'padding': '10px'}),
        ]),
        
        html.Div([
            html.Div([
                html.Label("Effect Size (δ₁)", style={'fontWeight': 'bold'}),
                dcc.Slider(
                    id='delta1-slider',
                    min=0.0, max=2.0, step=0.05, value=0.3,
                    marks={i/10: f'{i/10:.1f}' for i in range(0, 21, 2)},
                    tooltip={'placement': 'top', 'always_visible': True}
                ),
                html.P("Mean Sharpe ratio under alternative hypothesis",
                       style={'fontSize': '12px', 'color': '#7f8c8d'})
            ], style={'width': '48%', 'display': 'inline-block', 'padding': '10px'}),
            
            html.Div([
                html.Label("Rejection Threshold (c)", style={'fontWeight': 'bold'}),
                dcc.Input(
                    id='threshold-input',
                    type='number', value=1.96, step=0.01, min=0, max=5,
                    style={'width': '100%', 'padding': '8px', 'fontSize': '16px'}
                ),
                html.P("Critical value for statistical significance",
                       style={'fontSize': '12px', 'color': '#7f8c8d'})
            ], style={'width': '48%', 'display': 'inline-block', 'padding': '10px'}),
        ]),
        
        html.Div([
            html.Button("🔄 Reset to Defaults", id='reset-button', 
                       style={'padding': '10px 20px', 'fontSize': '14px', 
                              'backgroundColor': '#3498db', 'color': 'white',
                              'border': 'none', 'borderRadius': '5px', 'cursor': 'pointer'}),
            html.Div(id='preset-buttons', style={'display': 'inline-block', 'marginLeft': '20px'}),
        ], style={'marginTop': '15px'}),
    ], style={'padding': '20px', 'backgroundColor': 'white', 'margin': '20px', 
              'borderRadius': '10px', 'boxShadow': '0 2px 5px rgba(0,0,0,0.1)'}),
    
    # Metrics Cards
    html.Div(id='metrics-cards', style={'padding': '0 20px'}),
    
    # Main Visualization Tabs
    html.Div([
        dcc.Tabs([
            dcc.Tab(label='📊 Distributions', children=[
                html.Div([
                    dcc.Graph(id='distribution-plot')
                ], style={'padding': '20px'}),
                html.Div([
                    html.H5("Understanding the Plot", style={'color': '#2c3e50'}),
                    html.Ul([
                        html.Li("The null distribution (blue) represents strategies with zero true alpha"),
                        html.Li("The alternative distribution (green) represents strategies with true predictive power"),
                        html.Li("The mixture (orange) combines both based on π₀"),
                        html.Li("The selected maximum (red) shows the distribution after choosing the best of K trials"),
                        html.Li("The dotted line marks the rejection threshold; area to the right is the rejection region")
                    ], style={'color': '#7f8c8d', 'lineHeight': '1.8'})
                ], style={'padding': '0 40px 30px'})
            ]),
            
            dcc.Tab(label='📈 FDR Evolution', children=[
                html.Div([
                    dcc.Graph(id='fdr-evolution-plot')
                ], style={'padding': '20px'}),
                html.Div([
                    html.H5("Key Insights", style={'color': '#2c3e50'}),
                    html.Ul([
                        html.Li("FDR increases monotonically with search intensity K"),
                        html.Li("Even modest search (K=5) can triple the FDR compared to single-trial assumption"),
                        html.Li("The blue dashed lines show literature estimates (5-15%) that ignore search"),
                        html.Li("Type I error inflates rapidly while Type II error decreases")
                    ], style={'color': '#7f8c8d', 'lineHeight': '1.8'})
                ], style={'padding': '0 40px 30px'})
            ]),
            
            dcc.Tab(label='🎯 Sensitivity Analysis', children=[
                html.Div([
                    dcc.Graph(id='sensitivity-heatmap')
                ], style={'padding': '20px'}),
                html.Div([
                    dcc.Graph(id='identification-plot')
                ], style={'padding': '20px'}),
                html.Div([
                    html.H5("Identification Failure Explained", style={'color': '#2c3e50'}),
                    html.P([
                        "The right plot demonstrates ", html.B("observational equivalence"), ": ",
                        "Two completely different data-generating processes produce nearly identical ",
                        "observable outcomes. Case A has high null prevalence (75%) with search (K=5), ",
                        "while Case B has low null prevalence (10%) without search. Yet their conditional ",
                        "tail probabilities are almost indistinguishable, making FDR unidentifiable without ",
                        "explicit modeling of the search process."
                    ], style={'color': '#7f8c8d', 'lineHeight': '1.8'})
                ], style={'padding': '0 40px 30px'})
            ]),
            
            dcc.Tab(label='📋 Results Table', children=[
                html.Div([
                    html.H4("Parameter Sweep Results", style={'color': '#2c3e50', 'textAlign': 'center'}),
                    html.Div(id='results-table', style={'padding': '20px', 'overflowX': 'auto'})
                ])
            ]),
        ], style={'marginBottom': '20px'})
    ]),
    
    # Footer
    html.Div([
        html.Hr(),
        html.P([
            "Based on: López de Prado, M. (2026). ", 
            html.I('"What is the False Discovery Rate in Finance?"'),
            " SSRN:6450418 | ",
            "Dashboard created for educational purposes"
        ], style={'textAlign': 'center', 'color': '#95a5a6', 'fontSize': '12px'})
    ], style={'padding': '20px', 'backgroundColor': '#ecf0f1'})
])

# ============================================================
# CALLBACKS
# ============================================================

@app.callback(
    [Output('metrics-cards', 'children'),
     Output('distribution-plot', 'figure'),
     Output('fdr-evolution-plot', 'figure'),
     Output('sensitivity-heatmap', 'figure'),
     Output('identification-plot', 'figure'),
     Output('results-table', 'children')],
    [Input('k-slider', 'value'),
     Input('pi0-slider', 'value'),
     Input('delta1-slider', 'value'),
     Input('threshold-input', 'value')]
)
def update_dashboard(K, pi0, delta1, c):
    """Update all dashboard components based on user inputs."""
    
    # Fixed parameters for visualization (matching empirical calibration from paper)
    # These values are estimated from the 212 predictors dataset
    sigma0 = 0.10
    sigma1 = 0.20
    
    # Generate metrics cards
    metrics = create_metrics_cards(pi0, delta1, sigma0, sigma1, K, c)
    
    # Generate plots
    dist_fig = create_distribution_plot(pi0, delta1, sigma0, sigma1, K, c)
    fdr_fig = create_fdr_evolution_plot(pi0, delta1, sigma0, sigma1, c)
    sensitivity_fig = create_sensitivity_heatmap(delta1, sigma0, sigma1, c)
    ident_fig = create_identification_failure_plot()
    
    # Generate results table for K sweep
    K_sweep = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 30]
    table_data = []
    
    for k_val in K_sweep:
        errors = compute_error_rates(pi0, delta1, sigma0, sigma1, k_val, c)
        table_data.append({
            'K': k_val,
            'π₀': f'{pi0:.3f}',
            'α_K': f"{errors['alpha_K']:.3f}",
            'β_K': f"{errors['beta_K']:.3f}",
            'Power': f"{errors['power']:.3f}",
            'FDR': f"{errors['fdr']:.3f}"
        })
    
    df_results = pd.DataFrame(table_data)
    
    # Highlight row for K=5 (optimal fit in paper)
    table_html = html.Table([
        html.Thead([
            html.Tr([html.Th(col, style={'padding': '10px', 'backgroundColor': '#3498db', 'color': 'white'}) 
                    for col in df_results.columns])
        ]),
        html.Tbody([
            html.Tr([
                html.Td(row[col], style={
                    'padding': '8px',
                    'textAlign': 'center',
                    'backgroundColor': '#e74c3c' if row['K'] == 5 else 'white',
                    'color': 'white' if row['K'] == 5 else 'black',
                    'fontWeight': 'bold' if row['K'] == 5 else 'normal'
                })
                for col in df_results.columns
            ], style={'backgroundColor': '#f9f9f9' if i % 2 == 0 else 'white'})
            for i, (_, row) in enumerate(df_results.iterrows())
        ])
    ], style={'borderCollapse': 'collapse', 'width': '100%', 'margin': '0 auto',
              'boxShadow': '0 2px 5px rgba(0,0,0,0.1)'})
    
    return metrics, dist_fig, fdr_fig, sensitivity_fig, ident_fig, table_html

@app.callback(
    [Output('k-slider', 'value'),
     Output('pi0-slider', 'value'),
     Output('delta1-slider', 'value'),
     Output('threshold-input', 'value')],
    [Input('reset-button', 'n_clicks')],
    prevent_initial_call=True
)
def reset_parameters(n_clicks):
    """Reset all parameters to defaults."""
    return 5, 0.75, 0.3, 1.96

# ============================================================
# MAIN EXECUTION
# ============================================================

if __name__ == '__main__':
    print("="*70)
    print("🚀 Starting FDR Analysis Dashboard")
    print("="*70)
    print("\nDashboard features:")
    print("  • Interactive parameter exploration")
    print("  • Real-time distribution visualization")
    print("  • FDR evolution analysis")
    print("  • Sensitivity heatmaps")
    print("  • Identification failure demonstration")
    print("\n🌐 Opening dashboard at: http://127.0.0.1:8050")
    print("\nPress CTRL+C to exit\n")
    print("="*70)
    
    app.run(debug=True, host='127.0.0.1', port=8050)
