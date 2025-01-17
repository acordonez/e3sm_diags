from __future__ import print_function

import os

import cartopy.crs as ccrs
import cdutil
import matplotlib
import numpy as np
import numpy.ma as ma
from cartopy.mpl.ticker import LatitudeFormatter, LongitudeFormatter
from numpy.polynomial.polynomial import polyfit

from e3sm_diags.derivations.default_regions import regions_specs
from e3sm_diags.driver.utils.general import get_output_dir
from e3sm_diags.logger import custom_logger
from e3sm_diags.plot import get_colormap

matplotlib.use("Agg")
import matplotlib.colors as colors  # isort:skip  # noqa: E402
import matplotlib.pyplot as plt  # isort:skip  # noqa: E402

logger = custom_logger(__name__)

plotTitle = {"fontsize": 11.5}
plotSideTitle = {"fontsize": 9.5}

# Position and sizes of subplot axes in page coordinates (0 to 1)
panel = [
    (0.1691, 0.6810, 0.6465, 0.2258),
    (0.1691, 0.3961, 0.6465, 0.2258),
    (0.1691, 0.1112, 0.6465, 0.2258),
]

# Border padding relative to subplot axes for saving individual panels
# (left, bottom, right, top) in page coordinates
border = (-0.06, -0.03, 0.13, 0.03)


def add_cyclic(var):
    lon = var.getLongitude()
    return var(longitude=(lon[0], lon[0] + 360.0, "coe"))


def get_ax_size(fig, ax):
    bbox = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
    width, height = bbox.width, bbox.height
    width *= fig.dpi
    height *= fig.dpi
    return width, height


def determine_tick_step(degrees_covered):
    if degrees_covered > 180:
        return 60
    if degrees_covered > 60:
        return 30
    elif degrees_covered > 20:
        return 10
    else:
        return 1


def plot_panel_map(
    n, fig, proj, var, clevels, cmap, title, parameter, conf=None, stats={}
):

    var = add_cyclic(var)
    lon = var.getLongitude()
    lat = var.getLatitude()
    var = ma.squeeze(var.asma())

    # Contour levels
    levels = None
    norm = None
    if len(clevels) > 0:
        levels = [-1.0e8] + clevels + [1.0e8]
        norm = colors.BoundaryNorm(boundaries=levels, ncolors=256)

    # Contour plot
    ax = fig.add_axes(panel[n], projection=proj)
    region_str = parameter.regions[0]
    region = regions_specs[region_str]
    if "domain" in region.keys():  # type: ignore
        # Get domain to plot
        domain = region["domain"]  # type: ignore
    else:
        # Assume global domain
        domain = cdutil.region.domain(latitude=(-90.0, 90, "ccb"))
    kargs = domain.components()[0].kargs
    lon_west, lon_east, lat_south, lat_north = (0, 360, -90, 90)
    if "longitude" in kargs:
        lon_west, lon_east, _ = kargs["longitude"]
    if "latitude" in kargs:
        lat_south, lat_north, _ = kargs["latitude"]
    lon_covered = lon_east - lon_west
    lon_step = determine_tick_step(lon_covered)
    xticks = np.arange(lon_west, lon_east, lon_step)
    # Subtract 0.50 to get 0 W to show up on the right side of the plot.
    # If less than 0.50 is subtracted, then 0 W will overlap 0 E on the left side of the plot.
    # If a number is added, then the value won't show up at all.
    xticks = np.append(xticks, lon_east - 0.50)
    lat_covered = lat_north - lat_south
    lat_step = determine_tick_step(lat_covered)
    yticks = np.arange(lat_south, lat_north, lat_step)
    yticks = np.append(yticks, lat_north)
    ax.set_extent([lon_west, lon_east, lat_south, lat_north], crs=proj)
    cmap = get_colormap(cmap, parameter)
    contours = ax.contourf(
        lon,
        lat,
        var,
        transform=ccrs.PlateCarree(),
        norm=norm,
        levels=levels,
        cmap=cmap,
        extend="both",
    )

    if conf is not None:
        conf = add_cyclic(conf)
        conf = ma.squeeze(conf.asma())
        # Values in conf will be either 0 or 1. Thus, there are only two levels -
        # represented by the no-hatching and hatching levels.
        ax.contourf(
            lon,
            lat,
            conf,
            2,
            transform=ccrs.PlateCarree(),
            norm=norm,
            colors="none",
            extend="both",
            hatches=[None, "//"],
        )
    # Full world would be aspect 360/(2*180) = 1
    ax.set_aspect((lon_east - lon_west) / (2 * (lat_north - lat_south)))
    ax.coastlines(lw=0.3)
    if title[0] is not None:
        ax.set_title(title[0], loc="left", fontdict=plotSideTitle)
    if title[1] is not None:
        ax.set_title(title[1], fontdict=plotTitle)
    if title[2] is not None:
        ax.set_title(title[2], loc="right", fontdict=plotSideTitle)
    ax.set_xticks(xticks, crs=ccrs.PlateCarree())
    ax.set_yticks(yticks, crs=ccrs.PlateCarree())
    lon_formatter = LongitudeFormatter(zero_direction_label=True, number_format=".0f")
    lat_formatter = LatitudeFormatter()
    ax.xaxis.set_major_formatter(lon_formatter)
    ax.yaxis.set_major_formatter(lat_formatter)
    ax.tick_params(labelsize=8.0, direction="out", width=1)
    ax.xaxis.set_ticks_position("bottom")
    ax.yaxis.set_ticks_position("left")
    # Place a vertical line in the middle of the plot - i.e. 180 degrees
    ax.axvline(x=0.5, color="k", linewidth=0.5)

    # Color bar
    cbax = fig.add_axes((panel[n][0] + 0.6635, panel[n][1] + 0.0115, 0.0326, 0.1792))
    cbar = fig.colorbar(contours, cax=cbax)
    w, h = get_ax_size(fig, cbax)

    if levels is None:
        cbar.ax.tick_params(labelsize=9.0, length=0)

    else:
        maxval = np.amax(np.absolute(levels[1:-1]))
        if maxval < 1.0:
            fmt = "%5.3f"
            pad = 30
        elif maxval < 10.0:
            fmt = "%5.2f"
            pad = 25
        elif maxval < 100.0:
            fmt = "%5.1f"
            pad = 25
        else:
            fmt = "%6.1f"
            pad = 30
        cbar.set_ticks(levels[1:-1])
        labels = [fmt % level for level in levels[1:-1]]
        cbar.ax.set_yticklabels(labels, ha="right")
        cbar.ax.tick_params(labelsize=9.0, pad=pad, length=0)

    # Display stats
    if stats:
        top_stats = (stats["max"], stats["min"], stats["mean"], stats["std"])
        top_text = "Max\nMin\nMean\nSTD"
        fig.text(
            panel[n][0] + 0.6635,
            panel[n][1] + 0.2107,
            top_text,
            ha="left",
            fontdict=plotSideTitle,
        )
        fig.text(
            panel[n][0] + 0.7635,
            panel[n][1] + 0.2107,
            "%.2f\n%.2f\n%.2f\n%.2f" % top_stats,
            ha="right",
            fontdict=plotSideTitle,
        )

        if "rmse" in stats.keys():
            bottom_stats = (stats["rmse"], stats["corr"])
            bottom_text = "RMSE\nCORR"
            fig.text(
                panel[n][0] + 0.6635,
                panel[n][1] - 0.0205,
                bottom_text,
                ha="left",
                fontdict=plotSideTitle,
            )
            fig.text(
                panel[n][0] + 0.7635,
                panel[n][1] - 0.0205,
                "%.2f\n%.2f" % bottom_stats,
                ha="right",
                fontdict=plotSideTitle,
            )

    # Hatch text
    if conf is not None:
        hatch_text = "Hatched when pvalue < 0.05"
        fig.text(
            panel[n][0] + 0.25,
            panel[n][1] - 0.0355,
            hatch_text,
            ha="right",
            fontdict=plotSideTitle,
        )


def plot_map(
    reference,
    test,
    diff,
    metrics_dict,
    ref_confidence_levels,
    test_confidence_levels,
    parameter,
):
    if parameter.backend not in ["cartopy", "mpl", "matplotlib"]:
        return

    # Create figure, projection
    fig = plt.figure(figsize=parameter.figsize, dpi=parameter.dpi)
    # Use 179.99 as central longitude due to https://github.com/SciTools/cartopy/issues/946
    # proj = ccrs.PlateCarree(central_longitude=180)
    proj = ccrs.PlateCarree(central_longitude=179.99)

    # Use non-regridded test and ref for stats,
    # so we have the original stats displayed

    # First panel
    plot_panel_map(
        0,
        fig,
        proj,
        test,
        parameter.contour_levels,
        parameter.test_colormap,
        (parameter.test_name_yrs, parameter.test_title, test.units),
        parameter,
        conf=test_confidence_levels,
        stats=metrics_dict["test"],
    )

    # Second panel
    plot_panel_map(
        1,
        fig,
        proj,
        reference,
        parameter.contour_levels,
        parameter.reference_colormap,
        (parameter.ref_name_yrs, parameter.reference_title, reference.units),
        parameter,
        conf=ref_confidence_levels,
        stats=metrics_dict["ref"],
    )

    # Third panel
    plot_panel_map(
        2,
        fig,
        proj,
        diff,
        parameter.diff_levels,
        parameter.diff_colormap,
        (None, parameter.diff_title, test.units),
        parameter,
        stats=metrics_dict["diff"],
    )

    # Figure title
    fig.suptitle(parameter.main_title, x=0.5, y=0.97, fontsize=15)

    # Prepare to save figure
    # get_output_dir => {parameter.results_dir}/{set_name}/{parameter.case_id}
    # => {parameter.results_dir}/enso_diags/{parameter.case_id}
    output_dir = get_output_dir(parameter.current_set, parameter)
    if parameter.print_statements:
        logger.info("Output dir: {}".format(output_dir))
    # get_output_dir => {parameter.orig_results_dir}/{set_name}/{parameter.case_id}
    # => {parameter.orig_results_dir}/enso_diags/{parameter.case_id}
    original_output_dir = get_output_dir(parameter.current_set, parameter)
    if parameter.print_statements:
        logger.info("Original output dir: {}".format(original_output_dir))
    # parameter.output_file is defined in e3sm_diags/driver/enso_diags_driver.py
    # {parameter.results_dir}/enso_diags/{parameter.case_id}/{parameter.output_file}
    file_path = os.path.join(output_dir, parameter.output_file)
    # {parameter.orig_results_dir}/enso_diags/{parameter.case_id}/{parameter.output_file}
    original_file_path = os.path.join(original_output_dir, parameter.output_file)

    # Save figure
    for f in parameter.output_format:
        f = f.lower().split(".")[-1]
        plot_suffix = "." + f
        plot_file_path = file_path + plot_suffix
        plt.savefig(plot_file_path)
        # Get the filename that the user has passed in and display that.
        original_plot_file_path = original_file_path + plot_suffix
        logger.info(f"Plot saved in: {original_plot_file_path}")

    # Save individual subplots
    for f in parameter.output_format_subplot:
        page = fig.get_size_inches()
        i = 0
        for p in panel:
            # Extent of subplot
            subpage = np.array(p).reshape(2, 2)
            subpage[1, :] = subpage[0, :] + subpage[1, :]
            subpage = subpage + np.array(border).reshape(2, 2)
            subpage = list(((subpage) * page).flatten())
            extent = matplotlib.transforms.Bbox.from_extents(*subpage)
            # Save subplot
            subplot_suffix = ".%i." % (i) + f
            subplot_file_path = file_path + subplot_suffix
            plt.savefig(subplot_file_path, bbox_inches=extent)
            # Get the filename that the user has passed in and display that.
            original_subplot_file_path = original_file_path + subplot_suffix
            logger.info(f"Sub-plot saved in: {original_subplot_file_path}")
            i += 1

    plt.close()


def plot_scatter(x, y, parameter):
    fig = plt.figure(figsize=parameter.figsize, dpi=parameter.dpi)
    test_color = "black"
    ref_color = "red"
    test_title = "Test" if parameter.test_title == "" else parameter.test_title
    if parameter.test_name_yrs:
        test_title += " : {}".format(parameter.test_name_yrs)
    ref_title = (
        "Reference" if parameter.reference_title == "" else parameter.reference_title
    )
    if parameter.ref_name_yrs:
        ref_title += " : {}".format(parameter.ref_name_yrs)
    # https://stackoverflow.com/questions/14827650/pyplot-scatter-plot-marker-size
    plt.scatter(
        x["test"],
        y["test"],
        label=test_title,
        color=test_color,
        marker="s",
        s=8,
    )
    plt.scatter(x["ref"], y["ref"], label=ref_title, color=ref_color, marker="o", s=8)
    for value_type in ["test", "ref"]:
        if value_type == "test":
            type_str = "Test"
            type_color = test_color
            x_range = (min(x["test"]), max(x["test"]))
        else:
            type_str = "Reference"
            type_color = ref_color
            x_range = (min(x["ref"]), max(x["ref"]))
        # https://stackoverflow.com/questions/35091879/merge-2-arrays-vertical-to-tuple-numpy
        # Two parallel lists of values
        values = np.array((x[value_type], y[value_type]))
        # Zip the values together (i.e., list of (x,y) instead of (list of x, list of y)
        values = values.T
        if y["var"] == "TAUX":
            value_strs = [""]
        else:
            value_strs = ["positive ", "negative "]
        for value_str in value_strs:
            # https://stackoverflow.com/questions/24219841/numpy-where-on-a-2d-matrix
            if value_str == "positive ":
                # For all rows (x,y), choose the rows where x > 0
                rows = np.where(values[:, 0] > 0)
                smaller_x_range = (0, x_range[1])
                linestyle = "-"
            elif value_str == "negative ":
                # For all rows (x,y), choose the rows where x < 0
                rows = np.where(values[:, 0] < 0)
                smaller_x_range = (x_range[0], 0)
                linestyle = "--"
            elif value_str == "":
                rows = None
                smaller_x_range = x_range
                linestyle = "-"
            if rows:
                # Get the filtered zip (list of (x,y) where x > 0 or x < 0)
                filtered_values = values[rows]
            else:
                filtered_values = values
            # Get the filtered parallel lists (i.e., (list of x, list of y))
            filtered_values = filtered_values.T
            # https://stackoverflow.com/questions/19068862/how-to-overplot-a-line-on-a-scatter-plot-in-python
            b, m = polyfit(filtered_values[0], filtered_values[1], 1)
            label = "Linear fit for %sTS anomalies: %s (slope = %.2f)" % (
                value_str,
                type_str,
                m,
            )
            ys = [b + m * x for x in smaller_x_range]
            plt.plot(
                smaller_x_range,
                ys,
                label=label,
                color=type_color,
                linestyle=linestyle,
            )
    max_test = max(abs(min(y["test"])), abs(max(y["test"])))
    max_ref = max(abs(min(y["ref"])), abs(max(y["ref"])))
    max_value = max(max_test, max_ref) + 1
    plt.ylim(-max_value, max_value)
    plt.xlabel("{} anomaly ({})".format(x["var"], x["units"]))
    plt.ylabel("{} anomaly ({})".format(y["var"], y["units"]))
    plt.legend()

    # Prepare to save figure
    # get_output_dir => {parameter.results_dir}/{set_name}/{parameter.case_id}
    # => {parameter.results_dir}/enso_diags/{parameter.case_id}
    output_dir = get_output_dir(parameter.current_set, parameter)
    if parameter.print_statements:
        logger.info("Output dir: {}".format(output_dir))
    # get_output_dir => {parameter.orig_results_dir}/{set_name}/{parameter.case_id}
    # => {parameter.orig_results_dir}/enso_diags/{parameter.case_id}
    original_output_dir = get_output_dir(parameter.current_set, parameter)
    if parameter.print_statements:
        logger.info("Original output dir: {}".format(original_output_dir))
    # parameter.output_file is defined in e3sm_diags/driver/enso_diags_driver.py
    # {parameter.results_dir}/enso_diags/{parameter.case_id}/{parameter.output_file}
    file_path = os.path.join(output_dir, parameter.output_file)
    # {parameter.orig_results_dir}/enso_diags/{parameter.case_id}/{parameter.output_file}
    original_file_path = os.path.join(original_output_dir, parameter.output_file)

    # Figure title
    fig.suptitle(parameter.main_title, x=0.5, y=0.93, fontsize=15)

    # Save figure
    for f in parameter.output_format:
        f = f.lower().split(".")[-1]
        plot_suffix = "." + f
        plot_file_path = file_path + plot_suffix
        plt.savefig(plot_file_path)
        # Get the filename that the user has passed in and display that.

        original_plot_file_path = original_file_path + plot_suffix
        logger.info(f"Plot saved in: {original_plot_file_path}")

    plt.close()
