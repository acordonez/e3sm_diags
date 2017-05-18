import os
import copy
import vcs
import cdms2
from genutil import udunits
from acme_diags.driver.utils import get_output_dir


def plot(ref, test, diff, metrics_dict, parameters):
    # Line options, see here: https://uvcdat.llnl.gov/documentation/vcs/vcs-10.html
    # Other options not in the above link: https://uvcdat.llnl.gov/docs/vcs/graphics/unified1D.html
    ref_plot_linetype = 0
    ref_plot_color = 1  # 6 to 239
    ref_plot_width = 3  # 1 to 100
    ref_plot_marker = 1
    ref_plot_markersize = 1
    ref_plot_markercolor = 1

    test_plot_linetype = 0
    test_plot_color = 215
    test_plot_width = 3
    test_plot_marker = 1
    test_plot_markersize = 1
    test_plot_markercolor = 215

    # default ref breaks for now
    ref = test + 50

    vcs_canvas = vcs.init()
    vcs_canvas.geometry(1212, 1628)
    vcs_canvas.drawlogooff()

    # use vcs_canvas.show('colormap') to view all colormaps
    vcs_canvas.setcolormap('rainbow')  # 6 to 239 are purple to red in rainbow order

    ref_test_template = vcs.createtemplate('ref_test_template')
    # make all of the elements listed have priority = 0
    ref_test_template.blank(["mean", "max", "min", "zvalue", "dataname", "crtime","ytic2", "xtic2"])

    # the actual box around the plot
    ref_test_template.box1.x1 = 0.123
    ref_test_template.box1.x2 = 0.86
    ref_test_template.box1.y1 = 0.55
    ref_test_template.box1.y2 = 0.90

    # data (the lines) need to be offset accordingly
    ref_test_template.data.x1 = 0.123
    ref_test_template.data.x2 = 0.86
    ref_test_template.data.y1 = 0.55
    ref_test_template.data.y2 = 0.90

    #ref_test_template.dataname.x = 0.123
    #ref_test_template.dataname.y = 0.96

    ref_test_template.legend.x1 = 0.88
    ref_test_template.legend.x2 = 0.98
    ref_test_template.legend.y1 = 0.86
    ref_test_template.legend.y2 = 0.88
    #print ref_test_template.legend.texttable
    ref_test_template.legend.textorientation = 'defright'
    #print '-'*20
    #print ref_test_template.legend.texttable
    
    #help(ref_test_template.legend.textorientation.center)
    #print(ref_test_template.legend.textorientation.center()) 
    #quit()

    ref_test_template.title.x = 0.5
    ref_test_template.title.y = 0.92
    ref_test_template.title.textorientation = 'defcenter'

    ref_test_template.units.x = 0.855
    ref_test_template.units.y = 0.91

    # labels on xaxis
    ref_test_template.xlabel1.y = (0.55) - 0.02  # no xlabel1.x attribute

    # actual ticks
    ref_test_template.xtic1.y1 = (0.55 - 0.005) + 0.01
    ref_test_template.xtic1.y2 = (0.55 - 0.005)

    # name of xaxis
    ref_test_template.xname.y += 0.29


    # labels on yaxis
    ref_test_template.ylabel1.x = 0.1108  # no ylabel1.y attribute

    # actual ticks
    ref_test_template.ytic1.x1 = (0.123 - 0.005) + 0.01
    ref_test_template.ytic1.x2 = (0.123 - 0.005)

    # name of yaxis
    ref_test_template.yname.x += 0.05
    ref_test_template.yname.y += 0.17



    ref_line = vcs_canvas.createxvsy('ref_plot')
    ref_line.datawc_y1 = min(ref.min(), test.min())
    ref_line.datawc_y2 = max(ref.max(), test.max())

    test_line = vcs_canvas.createxvsy('test_plot')
    test_line.datawc_y1 = min(ref.min(), test.min())
    test_line.datawc_y2 = max(ref.max(), test.max())

    ref_line.line = ref_plot_linetype
    # ref_line.linetype = ref_plot_linetype
    ref_line.linecolor = ref_plot_color
    ref_line.linewidth = ref_plot_width
    ref_line.marker = ref_plot_marker
    ref_line.markersize = ref_plot_markersize
    ref_line.markercolor = ref_plot_markercolor

    test_line.line = test_plot_linetype
    # test_line.linetype = test_plot_linetype
    test_line.linecolor = test_plot_color
    test_line.linewidth = test_plot_width
    test_line.marker = test_plot_marker
    test_line.markersize = test_plot_markersize
    test_line.markercolor = test_plot_markercolor
    # test_line.smooth = 1

    blank_template = vcs_canvas.createtemplate('blank_template', ref_test_template)
    blank_template.blank()
    blank_template.legend.priority = 1
    blank_template.legend.y1 -= 0.05
    blank_template.legend.y2 -= 0.05

    vcs_canvas.plot(ref, ref_line, ref_test_template)
    vcs_canvas.plot(test, test_line, blank_template)
    vcs_canvas.png('set3vcs.png')
    vcs_canvas.clear()


def mask_by(input_var, maskvar, low_limit=None, high_limit=None):
    """masks a variable var to be missing except where maskvar>=low_limit and maskvar<=high_limit. 
    None means to omit the constrint, i.e. low_limit = -infinity or high_limit = infinity. var is changed and returned; we don't make a new variable.
    var and maskvar: dimensioned the same variables.
    low_limit and high_limit: scalars.
    """
    var = copy.deepcopy(input_var)
    if low_limit is None and high_limit is None:
        return var
    if low_limit is None and high_limit is not None:
        maskvarmask = maskvar > high_limit
    elif low_limit is not None and high_limit is None:
        maskvarmask = maskvar < low_limit
    else:
        maskvarmask = (maskvar < low_limit) | (maskvar > high_limit)
    if var.mask is False:
        newmask = maskvarmask
    else:
        newmask = var.mask | maskvarmask
    var.mask = newmask
    return var

def convert_units(var, target_units):
    ''' Converts units of var to target_units.
    var is a cdms.TransientVariable. '''

    if not hasattr(var, 'units') and var.id == 'SST':
        var.units = target_units
    elif not hasattr(var, 'units') and var.id =='ICEFRAC':
        var.units = target_units
        var = 100.0 * var
    elif var.units == 'fraction':
        var = 100.0 * var
        var.units = target_units
    elif var.units == 'mb':
        var.units = target_units
    elif var.units == 'gpm':  # geopotential meter
        var = var / 9.8 / 100  # convert to hecto meter
        var.units = target_units
    else:
        temp = udunits(1.0, var.units)
        coeff, offset = temp.how(target_units)
        var = coeff * var + offset
        var.units = target_units

    return var

if __name__ == '__main__':
    test_pth = '/Users/shaheen2/ACME_simulations/20160520.A_WCYCL1850.ne30_oEC.edison.alpha6_01_ANN_climo.nc'
    ref_pth = '/Users/shaheen2/obs_for_diagnostics/CRU_ANN_climo.nc'

    f = cdms2.open(ref_pth)
    ref = f('TREFHT_LAND')
    f.close()

    f = cdms2.open(test_pth)
    # TREFHT', 'LANDFRAC
    trefht = f('TREFHT')
    landfrac = f('LANDFRAC')
    test = mask_by(convert_units(trefht, target_units="K"), landfrac, low_limit=0.65)
    #test = convert_units(trefht, target_units="K")
    f.close()

    #diff = ref - test
    plot(ref, test, ref, None, None) 
