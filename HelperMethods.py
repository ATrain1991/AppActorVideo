def get_float_from_box_office(box_office):
    if box_office is None or box_office == '' or box_office == '-':
        return None
    if isinstance(box_office, (float, int)):
        return box_office
    else:
        box_office = box_office.replace('$','').replace(',','')
        if 'B' in box_office:
            return float(box_office.replace('B','')) * 1e9
        if 'M' in box_office:
            return float(box_office.replace('M','')) * 1e6
        elif 'K' in box_office:
            return float(box_office.replace('K','')) * 1e3
        else:
            return float(box_office)
