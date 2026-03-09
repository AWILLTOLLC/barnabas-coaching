#!/usr/bin/env python3
"""
Black Raven RFQ blast — sends to all manufacturers with valid emails.
CCs aaron@blackraven.com, saves to Posteo Sent folder.
"""

import smtplib, imaplib, json, time, email.utils
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

creds = json.load(open('/root/.openclaw/credentials/email.json'))
alias = creds['aliases']['august']

SUBJECT = 'RFQ: Custom 1" Scotch-Eye Auger Bit — 1,000 Unit Order'
CC = 'aaron@blackraven.com'

def make_body(company_name):
    return f'''Dear {company_name} Team,

My name is August Crane, and I am reaching out on behalf of Black Raven Company, a US-based manufacturer of traditional hand tools for the bushcraft and green woodworking markets.

We are seeking a manufacturing partner for a custom 1" Scotch-Eye Auger Bit and would like to request a quotation for production.

PRODUCT SPECIFICATION

  Product:       1" Scotch-Eye Auger Bit
  Material:      High Carbon Steel (1075 or equivalent)
  Finish:        Black Oxide
  Type:          Single-spur, aggressive lead screw, scotch-eye socket

  Overall Length:    8.000"
  Cutting Diameter:  1.000"
  Core Diameter:     0.500"
  Fluted Length:     5.375"
  Flute Pitch:       1.075" (5 full turns)
  Shank Diameter:    0.500"
  Shank Length:      0.750"
  Socket OD:         1.250"
  Socket ID (Bore):  1.000"
  Socket Height:     1.000"
  Lead Screw Length: 0.375"
  Lead Screw Dia.:   0.250"

CONSTRUCTION NOTES

  1. Scotch-Eye Socket: Cylindrical hollow socket welded to shank end. 1.250" OD,
     1.000" ID bore (0.125" wall). Accepts a hardwood dowel or natural branch as a
     T-handle. Weld must be ground smooth at the shank-to-socket transition.

  2. Lead Screw: Aggressive thread at tip to guide the auger and assist pulling
     through wood.

  3. Cutting Head: Single spur design, one cutting lip. Deburr all edges except
     cutting spur and lip, which must remain sharp.

  4. Helical Flute: 5 full turns at 1.075" pitch for chip evacuation.

  5. Finish: Black oxide on all surfaces. No paint or powder coat.

  6. Heat Treatment: Through-harden and temper entire piece (excluding socket).
     Optimized for cost over maximum edge retention. Socket left unhardened or
     welded on after heat treatment.

PRICING REQUEST

  Quantity 1:     Prototype / sample unit
  Quantity 50:    Small batch
  Quantity 250:   Production run
  Quantity 1,000: Volume pricing (primary interest)

Please include unit pricing, setup/tooling fees, lead times, and minimum order
requirements. We are open to requesting samples before placing a production order.

Shipping preference: FOB origin. CIF quote welcome if available.

We are actively evaluating manufacturing partners and would appreciate a response
within 2 weeks. If you have questions or need additional drawings/references,
please do not hesitate to contact me directly.

Thank you for your time. We look forward to the possibility of working with you.

Warm regards,

August Crane
Black Raven Company
Email: augustcrane@blackraven.com
Web:   www.blackraven.com
'''

# Manufacturers with valid direct emails (skip portal-only contacts)
manufacturers = [
    ("Hua Lung / King Drill Precision Tools", "hl@hualung.com.tw"),
    ("Rote Mate Industry Co., Ltd.", "info@rotemate.com"),
    ("SkillTek Industries Co., Ltd.", "sales@skilltek.com.tw"),
    ("ROTA Technology Inc.", "rotasales@rota.com.tw"),
    ("E Ding Tool Industrial Co., Ltd.", "peter@edingtools.com"),
    ("Haur Yueh Enterprise", "sales@haur-yueh.com"),
    ("Ajay Industries", "info@ajayind.com"),
    ("Varindera Tools Pvt. Ltd.", "info@varinderatools.com"),
    ("H.R. Industries (HRI Tools)", "info@hritools.com"),
    ("Eastman Cast & Forge Ltd.", "export05@eastmanhandtools.com"),
    ("Groz Engineering Tools Pvt. Ltd.", "info@groz-tools.com"),
    ("Hira Tools Corporation", "hiratools65@gmail.com"),
    ("Jhalani Tools / Ferreterro Tools LLP", "info@ferreterrotools.com"),
    ("JCBL Hand Tools", "info@jcblhandtools.com"),
    ("Hegde Agro Impex Pvt. Ltd.", "sales@hegde-agro.com"),
    ("Fasnna Group", "fasnna@gmail.com"),
    ("Royal Engineering Works", "royalengineering.wazirabad@gmail.com"),
    ("AM Industries Vietnam", "contact@aminds.com"),
    ("Wetool Hardware", "sales@welovetool.com"),
    ("AMS Vietnam", "info@amsviet.com"),
    ("Kuźnia Jawor", "kuznia@kuznia.com.pl"),
    ("MOB-IUS (Novalia)", "comercial@novalia.pro"),
    ("Fine Metal SRL", "export@finemetal.ro"),
    ("BeaverCraft Tools", "md@beavercraft.com.ua"),
    ("STRYI Carving Tools", "stryi.tools@gmail.com"),
    ("Sharky Forged Steel Tools", "marketing@forgedsteeltools.com"),
    ("URREA Herramientas Profesionales", "info@urrea.com"),
    ("Forged Mexico", "info@forgedmex.com"),
    ("FRISA Forjados", "sales@frisa.com"),
    ("Warwood Tool Company", "info@warwoodtool.com"),
    ("Baucor / Norck Inc.", "info@baucor.com"),
    ("Dawson Metal Company", "info@dawsonmetal.com"),
    ("Cornell Forge Company", "sales@cornellforge.com"),
    ("Steel Forge (North American Forgemasters)", "sales@steelforge.com"),
    ("Norseman Drill & Tool", "sales@norsemandrill.com"),
    ("Halder Group", "info@halder.de"),
    ("Poldi Steel (CP Forge)", "info@poldi-steel.com"),
    ("Tramontina", "export@tramontina.com.br"),
    ("Narex Tools", "narex@narex-nastroje.cz"),
    ("Perfect Tools Industries", "info@perfecttools.in"),
    ("Ajay Tools", "abhay@ajayind.com"),
    ("Solid Hand Tools Pvt. Ltd.", "info@solidhandtools.com"),
    ("GB Tools & Equipments", "export@gbtools.in"),
    ("Hira Industries International", "info@hiraindustries.in"),
    ("Hyatt Tools Pvt. Ltd.", "info@hyatttools.com"),
    ("Ogborn Nickel Corp", "sales@ogbornnickel.com"),
    ("DEECO Metals", "sales@deecometals.com"),
    ("Taiwan Trade Center (TAITRA)", "info@taitra.org.tw"),
    ("Wazirabad Industries", "wazirabadindustries@gmail.com"),
    ("AM Global Sourcing Vietnam", "sourcing@aminds.com"),
]

sent_log = []
skipped_log = []

def append_to_sent(imap, raw_bytes):
    imap.append('Sent', '\\Seen', imaplib.Time2Internaldate(time.time()), raw_bytes)

def make_msg(company, to_email):
    msg = MIMEMultipart()
    msg['From'] = f"{alias['name']} <{creds['username']}>"
    msg['Reply-To'] = alias['reply_to']
    msg['To'] = to_email
    msg['Cc'] = CC
    msg['Subject'] = SUBJECT
    msg['Date'] = email.utils.formatdate(localtime=True)
    msg['Message-ID'] = email.utils.make_msgid()
    msg.attach(MIMEText(make_body(company), 'plain'))
    # Normalize line endings to CRLF for SMTP compliance
    raw = msg.as_string().replace('\r\n', '\n').replace('\n', '\r\n').encode()
    return msg, raw

with imaplib.IMAP4_SSL('posteo.de', 993) as imap:
    imap.login(creds['username'], creds['password'])

    for company, to_email in manufacturers:
        try:
            msg, raw = make_msg(company, to_email)
            recipients = [to_email, CC]

            # Fresh SMTP connection per batch to avoid timeout drops
            with smtplib.SMTP(creds['smtp_host'], creds['smtp_port']) as smtp:
                smtp.starttls()
                smtp.login(creds['username'], creds['password'])
                smtp.sendmail(creds['username'], recipients, raw)

            append_to_sent(imap, raw)
            sent_log.append((company, to_email))
            print(f"✓ Sent: {company} <{to_email}>")
            time.sleep(3)

        except Exception as e:
            skipped_log.append((company, to_email, str(e)))
            print(f"✗ Failed: {company} <{to_email}> — {e}")

print(f"\n--- DONE ---")
print(f"Sent: {len(sent_log)}")
print(f"Failed: {len(skipped_log)}")
if skipped_log:
    print("\nFailed list:")
    for c, e, err in skipped_log:
        print(f"  {c} <{e}>: {err}")
