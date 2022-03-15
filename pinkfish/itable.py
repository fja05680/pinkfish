'''
Keep track of styles for cells/headers in PrettyTable.

The MIT License (MIT)

Copyright (c) 2014 Melissa Gymrek <mgymrek@mit.edu>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''

import pandas
import numpy


class TableStyle(object):

    """
    Keep track of styles for cells/headers in PrettyTable
    """

    def __init__(self, theme=None):
        self.row_head_style = CellStyle()
        self.col_head_style = CellStyle()
        self.cell_style = CellStyle()
        self.corner_style = CellStyle()

        # add themes as needed
        if theme == "basic":
            self.cell_style.set("border", "1px solid black")
            self.col_head_style.set("font-weight", "bold")
            self.row_head_style.set("font-weight", "bold")

        if theme == "theme1":
            self.cell_style.set("border", "1px solid black")
            self.cell_style.set("color", "black")
            self.col_head_style.set("color", "black")
            self.row_head_style.set("color", "black")
            self.col_head_style.set("font-weight", "bold")
            self.row_head_style.set("font_weight", "bold")
            self.col_head_style.set("background-color", "lightgray")
            self.row_head_style.set("background-color", "lightgray")


class CellStyle(object):

    """
    Styles for cells PrettyTable
    """

    def __init__(self):
        self.style_elements = {}  # dictionary of CSS property -> value
        self.format_function = None

    def set(self, key, value):
        self.style_elements[key] = value

    def css(self):
        style = ""
        for key in self.style_elements:
            style += "%s: %s;" % (key, self.style_elements[key])
        return style

    def column_format(self, x):
        if self.format_function is None:
            return str(x)
        else:
            try:
                return self.format_function(x)
            except:
                return str(x)

    def copy(self):
        c = CellStyle()
        c.style_elements = self.style_elements.copy()
        c.format_function = self.format_function
        return c


class PrettyTable(object):

    """
    Formatted tables for display in IPython notebooks
    """

    def __init__(self, df, tstyle=None, header_row=False, header_col=True, center=False, rpt_header=0):
        """
        df: pandas.DataFrame
        style: TableStyle
        header_row: include row headers
        header_col: include column headers
        """
        self.df = df
        self.num_rows = df.shape[0]
        self.num_cols = df.shape[1]
        self.header_row = header_row
        self.header_col = header_col
        self.style = tstyle
        self.center = center
        self.rpt_header = rpt_header

        # overall table style
        if tstyle is None:
            self.cell_style = CellStyle()
            self.corner_style = CellStyle()
            self.header_row_styles = [CellStyle()
                                      for i in range(self.num_rows)]
            self.header_col_styles = [CellStyle()
                                      for i in range(self.num_cols)]
            self.cell_styles = [[CellStyle() for i in range(self.num_cols)]
                                for j in range(self.num_rows)]
        else:
            self.cell_style = tstyle.cell_style
            self.corner_style = tstyle.corner_style
            self.header_row_styles = [
                tstyle.row_head_style.copy() for i in range(self.num_rows)]
            self.header_col_styles = [
                tstyle.col_head_style.copy() for i in range(self.num_cols)]
            self.cell_styles = [[self.cell_style.copy() for i in range(self.num_cols)]
                                for j in range(self.num_rows)]

    # functions to set styles
    def set_cell_style(self, style=None, tuples=None, rows=None, cols=None, format_function=None, **kwargs):
        """
        Apply cell style to rows and columns specified
        """
        if style is None:
            style = CellStyle()
        for key, value in kwargs.items():
            k = key.replace("_", "-")
            style.set(k, value)
        if format_function is not None:
            style.format_function = format_function
        if tuples:
            for tup in tuples:
                i = tup[0]
                j = tup[1]
                self.cell_styles[i][j] = style.copy()
        if rows is None and cols is None:
            return
        if rows is None:
            rows = range(self.num_rows)
        if cols is None:
            cols = range(self.num_cols)
        for i in rows:
            for j in cols:
                self.cell_styles[i][j] = style.copy()

    def set_row_header_style(self, style=None, indices=None, format_function=None, **kwargs):
        """
        Apply style to header at specific index
        If index is None, apply to all headings
        """
        if style is None:
            style = CellStyle()
        for key, value in kwargs.items():
            k = key.replace("_", "-")
            style.set(k, value)
        if format_function is not None:
            style.format_function = format_function
        if indices is None:
            indices = range(self.num_rows)
        for i in indices:
            self.header_row_styles[i] = style.copy()

    def set_col_header_style(self, style=None, indices=None, format_function=None, **kwargs):
        """
        Apply style to header at specific index
        If index is None, apply to all headings
        """
        if indices is None:
            indices = range(self.num_cols)
        if style is None:
            style = CellStyle()
        if format_function is not None:
            style.format_function = format_function
        for key, value in kwargs.items():
            k = key.replace("_", "-")
            style.set(k, value)
        for i in indices:
            self.header_col_styles[i] = style.copy()

    def set_corner_style(self, style=None, format_function=None, **kwargs):
        """
        Apply style to the corner cell
        """
        if style is None:
            style = CellStyle()
        for key, value in kwargs.items():
            k = key.replace("_", "-")
            style.set(k, value)
        if format_function is not None:
            style.format_function = format_function
        self.corner_style = style

    # functions to update styles
    def update_cell_style(self, rows=None, cols=None, format_function=None, **kwargs):
        """
        Update existing cell style
        """
        if rows is None:
            rows = range(self.num_rows)
        if cols is None:
            cols = range(self.num_cols)
        for i in rows:
            for j in cols:
                style = self.cell_styles[i][j]
                self.set_cell_style(
                    style=style, rows=[i], cols=[j], format_function=format_function, **kwargs)

    def update_row_header_style(self, indices=None, format_function=None, **kwargs):
        """
        Update existing row header tyle
        """
        if indices is None:
            indices = range(self.num_rows)
        for i in indices:
            style = self.header_row_styles[i]
            self.set_row_header_style(
                style=style, indices=[i], format_function=format_function, **kwargs)

    def update_col_header_style(self, indices=None, format_function=None, **kwargs):
        """
        Update existing row header tyle
        """
        if indices is None:
            indices = range(self.num_cols)
        for i in indices:
            style = self.header_col_styles[i]
            self.set_col_header_style(
                style=style, indices=[i], format_function=format_function, **kwargs)

    def update_corner_style(self, format_function=None, **kwargs):
        """
        Update the corner style
        """
        style = self.corner_style
        self.set_corner_style(
            style=style, format_function=format_function, **kwargs)

    # Functions to reset style
    def reset_cell_style(self, rows=None, cols=None):
        """
        Reset existing cell style to defaults
        """
        if rows is None:
            rows = range(self.num_rows)
        if cols is None:
            cols = range(self.num_cols)
        for i in rows:
            for j in cols:
                self.set_cell_style(style=CellStyle(), rows=[i], cols=[j])

    def reset_row_header_style(self, indices=None):
        """
        Reset row header style to defaults
        """
        if indices is None:
            indices = range(self.num_rows)
        for i in indices:
            self.set_row_header_style(style=CellStyle(), indices=[i])

    def reset_col_header_style(self, indices=None):
        """
        Reset col header style to defaults
        """
        if indices is None:
            indices = range(self.num_cols)
        for i in indices:
            self.set_col_header_style(style=CellStyle(), indices=[i])

    def reset_corner_style(self):
        """
        Reset corner style to defaults
        """
        style = self.corner_style
        self.set_corner_style(style=CellStyle())

    def _repr_html_(self):
        """
        IPython display protocol calls this method to get the
        HTML representation of the object
        """
        html = "<table style=\"%s\">" % self.cell_style.css()
        if self.header_col:
            html += "<tr style=\"%s\">" % self.cell_style.css()
            if self.header_row:
                # need to add an extra empty cell
                html += "<td style=\"%s\"></td>" % self.corner_style.css()
            for j in range(self.num_cols):
                if self.header_col_styles is not None:
                    header_style = self.header_col_styles[j].css()
                    header_data = self.header_col_styles[
                        j].column_format(self.df.columns[j])
                else:
                    header_style = self.cell_style.css()
                    header_data = self.cell_style.column_format(
                        self.df.columns[j])
                html += "<td style=\"%s\">" % header_style
                html += header_data
                html += "</td>"
            html += "</tr>"
        for i in range(self.num_rows):
            html += "<tr style=\"%s\">" % self.cell_style.css()
            if self.header_row:
                if self.header_row_styles is not None:
                    header_style = self.header_row_styles[i].css()
                    header_data = self.header_row_styles[
                        i].column_format(self.df.index.values[i])
                else:
                    header_style = self.cell_style.css()
                    header_data = self.cell_style.column_format(
                        self.df.index.values[i])
                html += "<td style=\"%s\">" % header_style
                html += header_data
                html += "</td>"
            for j in range(self.num_cols):
                if self.cell_styles[i][j] is not None:
                    col_style = self.cell_styles[i][j].css()
                    col_data = self.cell_styles[i][
                        j].column_format(self.df.iloc[i, j])
                else:
                    col_style = self.cell_style.css()
                    col_data = self.cell_style.column_format(
                        self.df.iloc[i, j])
                html += "<td style=\"%s\">" % col_style
                html += col_data
                html += "</td>"
            html += "</tr>"
            if self.rpt_header > 0 and (i + 1) % self.rpt_header == 0 and i < self.num_rows - 1:
                if self.header_col:
                    html += "<tr style=\"%s\">" % self.cell_style.css()
                    if self.header_row:
                        # need to add an extra empty cell
                        html += "<td style=\"%s\"></td>" % self.corner_style.css(
                        )
                    for j in range(self.num_cols):
                        if self.header_col_styles is not None:
                            header_style = self.header_col_styles[j].css()
                            header_data = self.header_col_styles[
                                j].column_format(self.df.columns[j])
                        else:
                            header_style = self.cell_style.css()
                            header_data = self.cell_style.column_format(
                                self.df.columns[j])
                        html += "<td style=\"%s\">" % header_style
                        html += header_data
                        html += "</td>"
                    html += "</tr>"
        html += "</table>"
        if self.center:
            return "<center>{html}</center>"
        else:
            return html

    def copy(self):
        p = PrettyTable(self.df, self.style, self.header_row, self.header_col)
        p.header_row_styles = [item.copy() for item in self.header_row_styles]
        p.header_col_styles = [item.copy() for item in self.header_col_styles]
        p.cell_styles = [[self.cell_styles[i][j].copy() for j in range(
            self.num_cols)] for i in range(self.num_rows)]
        p.corner_style = self.corner_style.copy()
        p.center = self.center
        return p
