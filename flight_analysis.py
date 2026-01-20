"""
Flight Delay Analysis Module

Over here, we are providing functions to analyze flight delay data

Functions:
    There are mainly 3 functions:
    display_counts: to calculate and display flight cancellations and diversions
    compute_combo_chart: to create combination of visualization
    prepare_geospatial_data: to refine data for geographic heatmap visualization
"""

import pandas as pd
import panel as pn
import hvplot.pandas
import geoviews as gv


def display_counts(df, year, airport, month, 
                   year_col='year', month_col='month', 
                   airport_col='airport_name',
                   cancelled_col='arr_cancelled', 
                   diverted_col='arr_diverted'):
    
    # Filter dataset to select criteria
    filtered_df = df[
        (df[year_col] == year) &
        (df[airport_col] == airport) &
        (df[month_col] == month)
    ]
    
    # Calculate totals
    if filtered_df.empty:
        cancelled = 0
        diverted = 0
    else:
        cancelled = int(filtered_df[cancelled_col].sum())
        diverted = int(filtered_df[diverted_col].sum())
    
    # Return formatted display
    return pn.Column(
        pn.pane.Markdown(f"### Flight Summary for **{airport}**"),
        pn.pane.Markdown(f"#### Year: **{year}**, Month: **{month}**"),
        pn.pane.Markdown(f"### Cancelled Flights: **{cancelled}**"),
        pn.pane.Markdown(f"### Diverted Flights: **{diverted}**")
    )


def compute_combo_chart(df, entity, factor, entity_options, delay_factors):
    
    # Extracting column names with selecyted entity
    name_col, code_col = entity_options[entity]
    
    # Calculating total delay
    df["total_delay"] = df[delay_factors].sum(axis=1)
    
    # Group by entity and aggregate delays
    grouped = (
        df.groupby([code_col, name_col])
        .sum()
        .reset_index()
    )
    
    top10 = grouped.sort_values("total_delay", ascending=False).head(10)
    
    # chart
    bar = top10.hvplot.bar(
        x=code_col,
        y="total_delay",
        color="blue",
        alpha=0.7,
        width=750,
        height=420,
        label="Total Delay",
        xrotation=90,
        hover_cols=[name_col, code_col]
    )
    
    # line chart
    line = top10.hvplot.line(
        x=code_col,
        y=factor,
        color="red",
        linewidth=3,
        marker="o",
        label=factor.replace('_', ' ').title(),
        hover_cols=[name_col, code_col]
    )
    
    # Overlay visulizations
    combo = (bar * line).opts(
        title=f"Top 10 {entity} — Total Delay vs {factor.replace('_',' ').title()}",
        legend_position="top_right"
    )
    
    return combo


def prepare_geospatial_data(df, coords_df, delay_cols, 
                            airport_col='airport',
                            iata_col='IATA Code'):
    
    # group airports and sum delays
    grouped = df.groupby(airport_col)[delay_cols].sum()
    
    # Calculate avg delay
    grouped['avg_delay_cause'] = grouped.mean(axis=1)
    
    # Reset index to make airport a column
    grouped = grouped.reset_index()
    
    # Merge with coordinate data
    merged = pd.merge(
        grouped,
        coords_df,
        left_on=airport_col,
        right_on=iata_col,
        how='left'
    )
    
    return merged


def create_geoviews_points(geo_data, size_factor=20, size_offset=5):
    points = gv.Points(
        geo_data,
        kdims=['longitude', 'latitude'],
        vdims=['avg_delay_cause', 'airport']
    ).opts(
        title="Average Delay by Airport",
        color='avg_delay_cause',
        cmap='Inferno_r',
        size=gv.dim('avg_delay_cause').norm() * size_factor + size_offset,
        alpha=0.8,
        colorbar=True,
        clabel='Avg Delay (Minutes)',
        tools=['hover'],
        width=900,
        height=500
    )
    
    return points


def validate_data(df, required_cols):

    results = {
        'missing_columns': [],
        'missing_values': {},
        'is_valid': True
    }
    
    # Missing columns
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        results['missing_columns'] = missing_cols
        results['is_valid'] = False
    
    # Missing values
    present_cols = [col for col in required_cols if col in df.columns]
    missing_vals = df[present_cols].isnull().sum()
    results['missing_values'] = missing_vals[missing_vals > 0].to_dict()
    
    if results['missing_values']:
        results['is_valid'] = False
    
    return results

def error_check(data):
    import holoviews as hv
    
    if data is None or len(data) == 0 or data['Minutes'].sum() == 0:
        return hv.Text(
            0.5, 0.5,
            "No delay data available\nfor this airline / airport"
        ).opts(
            width=800,
            height=500,
            text_align='center',
            text_baseline='middle',
            fontsize=14
        )
    return hv.Bars(
        data,
        kdims=['month', 'Delay Type'],
        vdims=['Minutes']
    )
