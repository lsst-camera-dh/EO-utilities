"""This module contains functions make run reports for EO test data.

"""

import sys

import os

import shutil

import xml.etree.ElementTree as ET

from xml.dom import minidom

import yaml

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.file_utils import makedir_safe,\
    get_raft_names_dc, read_runlist



def handle_file(file_name, outdir, action):
    """Move, copy or link a file to an output directory

    Parameters
    ----------
    file_name : `str`
        The file in question
    outdir : `str`
        The output directory
    action : `str`
        What to do with the file, of `copy`, `move`, or `link`

    Returns
    -------
    basename : `str`
        The basename of the file
    """
    basename = os.path.basename(file_name)
    if outdir is None:
        return basename

    inname = os.path.abspath(file_name)
    outname = os.path.abspath(os.path.join(outdir, basename))
    try:
        os.unlink(outname)
    except FileNotFoundError:
        pass

    if action in ['copy', 'cp']:
        shutil.copyfile(inname, outname)
    elif action in ['move', 'mv']:
        shutil.move(inname, outname)
    elif action in ['link', 'ln']:
        os.symlink(inname, outname)
    else:
        raise ValueError("Unknown action %s" % action)
    return basename




def create_report_header(root, **kwargs):
    """Make the header node for the report

    Parameters
    ----------
    root : `xml.etree.ElementTree.Element`
        The root node

    Keywords
    --------
    title : `str`
        The title for the HTML page
    stylesheet : `str`
        The css style sheet for the page

    Returns
    -------
    head : `xml.etree.ElementTree.SubElement`
        The header node

    """
    title = kwargs.get('title', None)
    stylesheet = kwargs.get('stylesheet', None)

    head = ET.SubElement(root, 'head')

    if title is not None:
        make_child_node(head, 'title', text=title)

    if stylesheet is not None:
        link = make_child_node(head, 'link',
                               href=stylesheet,
                               rel="StyleSheet")
        # This is out here b/c 'type' is a python keyword
        link.set('type', "text/css")

    return head




def make_child_node(parent_node, child_name, **kwargs):
    """Create a row in a table with a description and a plot

    Parameters
    ----------
    parent_node : `xml.etree.ElementTree.SubElement`
        The parent node
    chile_name : `str`
        The name of the child node

    Keywords
    --------
    text : `str`
        The text to write in the node
    node_class : `str`
        The css class to use for this node

    Remaining kwargs are set as attributes in the node

    Returns
    -------
    child_node : `xml.etree.ElementTree.SubElement`
        The child node
    """
    child_node = ET.SubElement(parent_node, child_name)
    for key, val in kwargs.items():
        if val is None:
            continue
        elif key == 'text':
            child_node.text = val
        elif key == 'node_class':
            child_node.set('class', val)
        else:
            child_node.set(key, val)
    return child_node


def create_plot_table_row(tbody_node, desc, plot_file, outdir, **kwargs):
    """Create a row in a table with a description and a plot

    Parameters
    ----------
    tbody_node : `xml.etree.ElementTree.SubElement`
        The table node
    desc : `str`
        The description of the plot
    plot_file : `str`
        The name of the file with the plot
    outdir : `str`
        The name of the directory the html is being written to

    Keywords
    --------
    plot_report_action : `str`
        What to do with the plot file, of `copy`, `move`, or `link`
    row_class : `str`
        The style class to use for the row node
    col_desc_class : `str`
        The style class to use for the description column node
    col_fig_class : `str`
        The style class to use for the figure column node
    col_img_class : `str`
        The style class to use for the figure image node

    Returns
    -------
    row_node : `xml.etree.ElementTree.SubElement`
        The row node
    """

    if not os.path.exists(plot_file):
        sys.stdout.write("Warning, skipping missing plot %s\n" % plot_file)

    basename = handle_file(plot_file, outdir, kwargs.get('plot_report_action', 'link'))

    row_node = make_child_node(tbody_node, 'tr', node_class=kwargs.get('row_class', None))
    make_child_node(row_node, 'td',
                    node_class=kwargs.get('col_desc_class', None),
                    text=desc)
    col_fig_node = make_child_node(row_node, 'td',
                                   node_class=kwargs.get('col_fig_class', None))

    col_fig_ref = make_child_node(col_fig_node, 'a', href=basename)
    make_child_node(col_fig_ref, 'img',
                    node_class=kwargs.get('col_img_class', None),
                    src=basename)

    return row_node


def create_slot_table(parent_node, **kwargs):
    """Create table with descriptions and a plots

    Parameters
    ----------
    parent_node : `xml.etree.ElementTree.SubElement`
        The parent node

    Keywords
    --------
    header_row_class : `str`
        The style class to use for the header row node
    header_col_class : `str`
        The style class to use for the header column node
    table_row_class : `str`
        The style class to use for the row node
    table_col_class : `str`
        The style class to use for the description column node

    Returns
    -------
    table_node : `xml.etree.ElementTree.SubElement`
        The table node
    """
    kwcopy = kwargs.copy()

    make_child_node(parent_node, 'h3', text="List of CCDs")

    table_node = make_child_node(parent_node, 'table')
    tbody_node = make_child_node(table_node, 'tbody')

    header_row_node = make_child_node(tbody_node, 'tr',
                                      node_class=kwcopy.get('header_row_class', None))
    make_child_node(header_row_node, 'td',
                    node_class=kwcopy.get('header_col_class', None),
                    text='SLOT')


    for slot in ALL_SLOTS:
        row_node = make_child_node(tbody_node, 'tr',
                                   node_class=kwcopy.get('table_row_class', None))
        col_node = make_child_node(row_node, 'td',
                                   node_class=kwcopy.get('table_col_class', None))
        make_child_node(col_node, 'a',
                        text=slot,
                        href="%s.html" % slot)

    return table_node



def create_plot_table(parent_node, table_desc, inputdir, outdir, **kwargs):
    """Create table with descriptions and a plots

    Parameters
    ----------
    parent_node : `xml.etree.ElementTree.SubElement`
        The parent node
    table_desc : `list`
        A list of dictionaries with the plots and the descriptions
    inpudir : `str`
        The name of the directory with the plots
    outdir : `str`
        The name of the directory the html is being written to

    Keywords
    --------
    kwargs are passed to create_plot_table_row

    Returns
    -------
    table_node : `xml.etree.ElementTree.SubElement`
        The table node
    """
    kwcopy = kwargs.copy()
    dataid = kwcopy.pop('dataid', None)

    table_node = make_child_node(parent_node, 'table')
    tbody_node = make_child_node(table_node, 'tbody')

    header_col_class = kwcopy.get('header_col_class', None)

    header_row_node = make_child_node(tbody_node, 'tr',
                                      node_class=kwcopy.get('header_row_class', None))
    make_child_node(header_row_node, 'td',
                    text="Description",
                    node_class=header_col_class)
    make_child_node(header_row_node, 'td',
                    text="Plot",
                    node_class=header_col_class)

    rowlist = table_desc['rows']
    for row_desc in rowlist:
        plotfile = os.path.join(inputdir, row_desc['figure'].format(**dataid))
        create_plot_table_row(tbody_node, row_desc['text'],
                              plotfile, outdir, **kwcopy)

    return table_node


def create_plot_tables(parent_node, table_dict, inputdir, outdir, **kwargs):
    """Create table with descriptions and a plots

    Parameters
    ----------
    parent_node : `xml.etree.ElementTree.SubElement`
        The parent node
    table_dict : `dict`
        A dictionaries with the table descriptions
    inpudir : `str`
        The name of the directory with the plots
    outdir : `str`
        The name of the directory the html is being written to

    Keywords
    --------
    kwargs are passed to create_plot_table_row

    Returns
    -------
    table_node : `xml.etree.ElementTree.SubElement`
        The table node
    """
    for _, tdesc in table_dict.items():
        make_child_node(parent_node, 'h3', text=tdesc.get('header_text', None))
        create_plot_table(parent_node, tdesc, inputdir, outdir, **kwargs)


def create_run_table(parent_node, dataset, **kwargs):
    """Create table with descriptions and a plots

    Parameters
    ----------
    parent_node : `xml.etree.ElementTree.SubElement`
        The parent node
    dataset : `str`
        The dataset identifier

    Returns
    -------
    table_node : `xml.etree.ElementTree.SubElement`
        The table node
    """
    kwcopy = kwargs.copy()

    runlist = read_runlist("%s_runs.txt" % dataset)

    make_child_node(parent_node, 'h3', text="List of runs")

    table_node = make_child_node(parent_node, 'table')
    tbody_node = make_child_node(table_node, 'tbody')

    header_row_node = make_child_node(tbody_node, 'tr',
                                      node_class=kwcopy.get('header_row_class', None))
    make_child_node(header_row_node, 'td',
                    text="RUN",
                    node_class=kwcopy.get('header_col_class', None))
    make_child_node(header_row_node, 'td',
                    text="RAFT",
                    node_class=kwcopy.get('header_col_class', None))

    for run_info in runlist:
        row_node = make_child_node(tbody_node, 'tr',
                                   node_class=kwcopy.get('table_row_class', None))
        col_run_node = make_child_node(row_node, 'td',
                                       node_class=kwcopy.get('table_col_class', None))
        raft = run_info[0].replace('-Dev', '')
        run_url = os.path.join(raft, run_info[1], 'index.html')

        make_child_node(col_run_node, 'a',
                        href=run_url,
                        text=run_info[1])
        make_child_node(row_node, 'td',
                        text=raft,
                        node_class=kwcopy.get('table_col_class', None))

    return table_node


def write_tree_to_html(tree, filepath=None):
    """Write a html file from an element tree

    Parameters
    ----------
    tree : `xml.etree.ElementTree.Element`
        The tree we are writing
    filepath : `str` or `None`
        Where to write the file
    """
    if filepath is None:
        outfile = sys.stdout
    else:
        outfile = open(filepath, 'w')

    rough_str = ET.tostring(tree)
    reparsed = minidom.parseString(rough_str)
    pretty_str = reparsed.toprettyxml(indent="  ")

    outfile.write(pretty_str)

    if filepath is not None:
        print("wrote %s" % filepath)
        outfile.close()


def write_slot_report(dataid, inputbase, outbase, **kwargs):
    """Create table with descriptions and a plots

    Parameters
    ----------
    dataid : `dict`
        Dictionary with run, raft, slot
    inputbase : `str`
        Input base directory
    outbase : `str` or `None`
        Output directory

    Keywords
    --------
    """
    kwcopy = kwargs.copy()

    sys.stdout.write("Writing report for {run}:{raft}:{slot}\n".format(**dataid))

    yamlfile = kwcopy.pop('template_file', 'html_report.yaml')
    cssfile_in = kwcopy.pop('css_file', 'style.css')
    template_dict = yaml.safe_load(open(yamlfile))
    table_desc = template_dict['slot_plot_tables']
    kwcopy.update(template_dict['defaults'])
    kwcopy['dataid'] = dataid

    if outbase is None:
        outdir = None
        html_file = None
    else:
        outdir = os.path.join(outbase, dataid['raft'], dataid['run'])
        html_file = os.path.join(outdir, '%s.html' % dataid['slot'])
        makedir_safe(html_file)
        handle_file(cssfile_in, outdir, action='copy')

    html_node = ET.Element('html')
    create_report_header(html_node,
                         title="TS8 Results for {run}:{raft}:{slot}".format(**dataid),
                         stylesheet=kwcopy.pop('stylesheet', 'style.css'))

    body_node = make_child_node(html_node, 'body')

    create_plot_tables(body_node, table_desc, inputbase, outdir, **kwcopy)
    write_tree_to_html(html_node, html_file)


def write_raft_report(dataid, inputbase, outbase, **kwargs):
    """Create table with descriptions and a plots

    Parameters
    ----------
    dataid : `dict`
        Dictionary with run, raft
    inputbase : `str`
        Input base directory
    outbase : `str` or `None`
        Output directory

    Keywords
    --------
    """
    kwcopy = kwargs.copy()

    sys.stdout.write("Writing report for {run}:{raft}\n".format(**dataid))

    yamlfile = kwcopy.pop('template_file', 'html_report.yaml')
    cssfile_in = kwcopy.pop('css_file', 'style.css')
    template_dict = yaml.safe_load(open(yamlfile))
    table_desc = template_dict['raft_plot_tables']
    kwcopy.update(template_dict['defaults'])
    kwcopy['dataid'] = dataid

    if outbase is None:
        outdir = None
        html_file = None
    else:
        outdir = os.path.join(outbase, dataid['raft'], dataid['run'])
        html_file = os.path.join(outdir, 'index.html')
        makedir_safe(html_file)
        handle_file(cssfile_in, outdir, action='copy')


    html_node = ET.Element('html')
    create_report_header(html_node,
                         title="TS8 Results for {run}:{raft}".format(**dataid),
                         stylesheet=kwcopy.pop('stylesheet', 'style.css'))

    body_node = make_child_node(html_node, 'body')

    create_plot_tables(body_node, table_desc, inputbase, outdir, **kwcopy)

    create_slot_table(body_node, **kwcopy)

    write_tree_to_html(html_node, html_file)



def write_run_report(run, inputbase, outbase, **kwargs):
    """Create table with descriptions and a plots

    Parameters
    ----------
    run : `str`
        Run number
    inputbase : `str`
        Input base directory
    outbase : `str` or `None`
        Output directory

    Keywords
    --------
    """
    sys.stdout.write("Writing report for %s\n" % run)

    rafts = get_raft_names_dc(run)

    for raft in rafts:
        dataid = dict(run=run, raft=raft)
        write_raft_report(dataid, inputbase, outbase, **kwargs)
        for slot in ALL_SLOTS:
            dataid['slot'] = slot
            write_slot_report(dataid, inputbase, outbase, **kwargs)


def write_summary_report(dataset, inputbase, outbase, **kwargs):
    """Create table with descriptions and a plots

    Parameters
    ----------
    dataset : `str`
        Dataset id
    inputbase : `str`
        Input base directory
    outbase : `str` or `None`
        Output directory

    """
    kwcopy = kwargs.copy()

    sys.stdout.write("Writing report for %s\n" % dataset)

    yamlfile = kwcopy.pop('template_file', 'html_report.yaml')
    cssfile_in = kwcopy.pop('css_file', 'style.css')
    template_dict = yaml.safe_load(open(yamlfile))
    table_desc = template_dict['summary_plot_tables']
    kwcopy.update(template_dict['defaults'])
    kwcopy['dataid'] = dict(dataset=dataset)

    if outbase is None:
        outdir = None
        html_file = None
    else:
        outdir = os.path.join(outbase)
        html_file = os.path.join(outdir, '%s.html' % dataset)
        makedir_safe(html_file)
        handle_file(cssfile_in, outdir, action='copy')

    html_node = ET.Element('html')
    create_report_header(html_node,
                         title="%s results" % dataset,
                         stylesheet=kwcopy.pop('stylesheet', 'style.css'))

    body_node = make_child_node(html_node, 'body')

    create_plot_tables(body_node, table_desc, inputbase, outdir, **kwcopy)

    create_run_table(body_node, dataset, **kwcopy)

    write_tree_to_html(html_node, html_file)



def write_dataset_reports(dataset, inputbase, outbase, **kwargs):
    """Create table with descriptions and a plots

    Parameters
    ----------
    dataset : `str`
        Dataset id
    inputbase : `str`
        Input base directory
    outbase : `str` or `None`
        Output directory

    """
    sys.stdout.write("Writing report for %s\n" % dataset)

    write_summary_report(dataset, inputbase, outbase, **kwargs)
    runlist = read_runlist("%s_runs.txt" % dataset)

    for run_info in runlist:
        write_run_report(run_info[1], inputbase, outbase, **kwargs)



if __name__ == '__main__':

    write_dataset_reports('ts8', 'analysis/ts8/plots', 'analysis/ts8/html')
