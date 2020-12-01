from itertools import chain

from IPython.display import display
import ipywidgets as widgets
import iccas as ic


def new_output(f, *args, **kwargs):
    out = widgets.Output(layout=widgets.Layout(margin='16px 8px'))
    with out:
        f(*args, **kwargs)
    return out


def form(fields, label_position="left"):
    if label_position not in {"left", "top"}:
        raise ValueError("label_position")

    if label_position == "left":
        grid_template_columns = "auto 1fr"
        label_layout = widgets.Layout(display="flex", justify_content="flex-end")
        children = list(
            chain.from_iterable(
                (widgets.Label(label + ":", layout=label_layout), control)
                for label, control in fields
            )
        )
    else:
        grid_template_columns = "max-content"
        children = [
            widgets.VBox(
                [widgets.Label(label + ":"), control], layout=widgets.Layout(margin="0")
            )
            for label, control in fields
        ]

    return widgets.GridBox(
        children=children,
        layout=widgets.Layout(
            grid_template_columns=grid_template_columns,
            grid_template_rows="max-content " * len(fields),
            grid_gap="8px",
        ),
    )


def with_interaction(f, controls, output_position="bottom", output=None):
    if output_position not in {"top", "right", "bottom", "left"}:
        raise ValueError("output_position")
    fixed_kwargs = {}
    bindings = {}
    form_fields = []
    for key, c in controls.items():
        if isinstance(c, widgets.fixed):
            fixed_kwargs[key] = c
            bindings[key] = c
        elif isinstance(c, tuple):
            form_fields.append(c)
            bindings[key] = c[1]
        else:
            raise TypeError(
                "invalid control entry: not a widgets.fixed() nor a tuple(label, control)"
            )

    is_vertical_layout = output_position in {"bottom", "top"}

    controls_form = form(
        form_fields, label_position="left" if is_vertical_layout else "top"
    )
    output = widgets.interactive_output(f, bindings)
    gap = widgets.Box(layout=widgets.Layout(width="32px", height="32px"))
    box_type = widgets.VBox if is_vertical_layout else widgets.HBox
    children = (
        [controls_form, gap, output]
        if output_position in {"bottom", "right"}
        else [output, gap, controls_form]
    )

    align_items = "center" if is_vertical_layout else "flex-start"
    return box_type(
        children=children, layout=widgets.Layout(margin="16px 0", align_items=align_items)
    )


def variable_form_field(value="cases"):
    return (
        "Casi / Decessi",
        widgets.Dropdown(
            value=value, options=[("Casi", "cases"), ("Decessi", "deaths")]
        ),
    )


def period_form_field(
    datetime_index, fmt="%d %b", value=None, **kwargs
):
    kwargs = {"continuous_update": False, **kwargs}
    if value is not None:
        series = datetime_index.to_series()
        start, end = value
        start = series.loc[start][0] if start else datetime_index[0]
        end = series.loc[end][0] if end else datetime_index[-1]
        kwargs["value"] = (start, end)
    elif "index" not in kwargs:
        kwargs["index"] = (0, len(datetime_index) - 1)
    return (
        "Periodo",
        widgets.SelectionRangeSlider(
            options=list(zip(datetime_index.strftime(fmt), datetime_index)), **kwargs
        ),
    )


def date_form_field(datetime_index, fmt="%d %b %Y", window_control=None, **kwargs):
    def make_options(start_index):
        datetimes = datetime_index[start_index:]
        return list(zip(datetimes.strftime(fmt), datetimes))

    start_index = window_control.value if window_control else 0
    args = {"continuous_update": False, **kwargs}
    widget = widgets.SelectionSlider(options=make_options(start_index), **args)
    if window_control:

        def set_options(c):
            start_index = c["new"]
            new_min_date = datetime_index[start_index]
            new_value = new_min_date if widget.value < new_min_date else widget.value
            widget.value = new_value
            widget.options = make_options(start_index)

        window_control.observe(set_options, "value")
    return "Data", widget


def age_group_size_form_field(value=20, min=10, max=90, step=10):
    return (
        "Ampiezza fasce d'età (anni)",
        widgets.IntSlider(min=min, max=max, step=step, value=value),
    )


def window_form_field(value=14, min=1, max=30, continuous_update=False, **kwargs):
    widget = widgets.IntSlider(
        min=min, max=max, value=value, continuous_update=continuous_update, **kwargs
    )
    return "Finestra temporale (giorni)", widget


def averages_by_period_table(
    data, variable, freq='M', normalize: bool = False,
    age_group_size=10, gradient_axis=1
):
    d = data[variable].drop(columns='unknown')
    d = ic.aggregate_age_groups(d, age_group_size)
    d = ic.average_by_period(d, freq=freq)

    if normalize:
        d = d.div(d.sum(axis=1), axis=0)
        fmt = '{:.1%}'
    else:
        fmt = '{:.0f}'

    label = 'casi' if variable == 'cases' else 'decessi'
    if freq == 'M':
        index_name = 'Mese'
        freq_label = 'mese per mese'
    else:
        index_name = 'Data di fine periodo'
        freq_label = f'periodi di {freq} giorni'
    caption = f'Numero medio di {label} giornalieri ({freq_label})'

    d.columns = d.columns.rename('Età')
    d.index = d.index.rename(index_name)
    return (
        d.style
        .format(fmt)
        .background_gradient(axis=gradient_axis)
        .set_caption(caption)
    )


def display_averages_by_period_table(
    data, variable, freq='M', normalize: bool = False,
    age_group_size=10, gradient_axis=1
):
    display(
        averages_by_period_table(
            data, variable, freq=freq, normalize=normalize,
            age_group_size=age_group_size, gradient_axis=gradient_axis
        )
    )
