import sys
from app.shared.utils.html_to_markdown import convert_html_to_markdown

user_sample_html = """<!DOCTYPE html>
<html lang="en-IN">
<head>
    <meta charset="UTF-8">
    <title>Document</title>
    <style>
body { padding: 0 !important; font-family: serif; }
p.paragraph { font-size: 12pt; }
    </style>
</head>
<body>
<div class="page-body-container">
<p class="paragraph">Regd. No.: XXX54826XX<br/><br/>Mr. Saubhik Bhaumik<br/>Age / Sex: 27 YRS / M<br/>Registered on: 17/10/2024 04:55 PM<br/>Collected on: 17/10/2024<br/>Reported on: 17/10/2024 04:55 PM<br/>Refered by: Self<br/>Reg. no.: 1001<br/><br/>LABSMART SOFTWARE<br/>Sample Letterhead<br/><br/>HAEMATOLOGY<br/>COMPLETE BLOOD COUNT(CBC)<br/><br/>TEST | VALUE | UNIT | REFERENCE<br/>HEMOGLOBIN | 15 | g/dl | 13 - 17<br/>TOTAL LEUKOCYTE COUNT | 5,100 | cumm | 4,800 - 10,800<br/>DIFFERENTIAL LEUCOCYTÉ COUNT<br/>NEUTROPHILS | 79 | % | 40 - 80<br/>LYMPHOCYTE L | 18 | % | 20 - 40<br/>EOSINOPHILS I | 1 | % | 1 - 6<br/>MONOCYTES L | 1 | % | 2 - 10<br/>BASOPHILS l | 1 | % | &lt; 2<br/>PLATELET COUNT | 3.5 | lakhs/cumm | 1.5 - 4.1<br/>TOTAL RBC COUNT | 5 | million/cumm | 4.5 - 5.5<br/>HEMATOCRIT VALUE, HCT | 42% | % | 40 - 50<br/>MEAN CORPUSCULAR VOLUME, MCV | 84.0 fL | | 83 - 101<br/>MEAN CELL HAEMOGLOBIN, MCH | 30.0 Pg | | 27 - 32<br/>MEAN CELL HAEMOGLOBIN CON, MCHC H | 35.7 % | | 31.5 - 34.5<br/><br/>Clinical Notes:<br/>A complete blood count(CBC) is used to evaluate overall health and detect a wide range of disorders, including anemia, infection, and leukemia.</p>
</div>
</body>
</html>"""

md = convert_html_to_markdown(user_sample_html)
print("=== CONVERTED MARKDOWN OUTPUT ===")
print(md)
