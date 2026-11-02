"""Small end-to-end check of the Soiledge workbook bridge."""
import io
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.api.soiledge import _evaluate, _read_xlsx


def make_workbook():
    headers = ["采样点编号", "有效磷（AP）（mg/kg）", "黏粒含量（Clay）%", "全磷（TP）(g/kg)",
               "速效钾（AK）（mg/kg）", "全氮（TN）风干基%", "阳离子交换量cmol（+）/kg（CEC）"]
    records = [["station-1", "3.08", "23", "1.11", "300.08", "0.31", "40"],
               ["station-2", "8", "25", "0.9", "151", "0.2", "20"]]
    rows = []
    for row_number, cells in enumerate([headers] + records, 1):
        contents = "".join(f'<c r="{chr(65 + index)}{row_number}" t="inlineStr"><is><t>{value}</t></is></c>'
                           for index, value in enumerate(cells))
        rows.append(f'<row r="{row_number}">{contents}</row>')
    xml = ('<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
           f'<sheetData>{"".join(rows)}</sheetData></worksheet>')
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("xl/worksheets/sheet1.xml", xml)
    return output.getvalue()


workbook = make_workbook()
parsed = _read_xlsx(workbook)
local = _evaluate(parsed, "玉米")
assert local["total"] == 2 and len(local["rows"]) == 2
request = urllib.request.Request("http://127.0.0.1:18001/api/soiledge/upload?crop=%E7%8E%89%E7%B1%B3",
                                 data=workbook, headers={"Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}, method="POST")
with urllib.request.urlopen(request, timeout=10) as response:
    remote = json.load(response)
assert remote == local
print("Soiledge XLSX parser, batch calculation, and local API: OK")
