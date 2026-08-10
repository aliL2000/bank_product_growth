"""Generate reports/Project_Recap.pdf — a plain-language project recap for a
non-ML audience. Content mirrors ROADMAP.md's Working Log; rerun this script
after updating the roadmap to keep the recap in sync.

Usage: python src/reports/generate_project_recap.py
"""

from pathlib import Path

from fpdf import FPDF

OUT_PATH = Path(__file__).resolve().parents[2] / "reports" / "Project_Recap.pdf"

TEAL = (16, 94, 107)
DARK = (30, 41, 59)
GRAY = (100, 110, 120)
BOX_BG = (237, 242, 245)
BOX_BORDER = (16, 94, 107)
BADGE_BG = (16, 94, 107)


class Recap(FPDF):
    def header(self):
        pass

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*GRAY)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def section_title(self, text):
        self.set_font("Helvetica", "B", 15)
        self.set_text_color(*TEAL)
        self.cell(0, 9, text, new_x="LMARGIN", new_y="NEXT")
        y = self.get_y()
        self.set_draw_color(*TEAL)
        self.set_line_width(0.6)
        self.line(self.l_margin, y, self.l_margin + 22, y)
        self.ln(4)

    def body(self, text, size=10.5, color=DARK, style=""):
        self.set_font("Helvetica", style, size)
        self.set_text_color(*color)
        self.multi_cell(0, 5.6, text, align="L", new_x="LMARGIN", new_y="NEXT")
        self.ln(1.5)

    def bullet(self, text):
        self.set_font("Helvetica", "", 10.5)
        self.set_text_color(*DARK)
        self.cell(4, 5.6, "-")
        self.multi_cell(
            self.epw - 4, 5.6, text, align="L", new_x="LMARGIN", new_y="NEXT"
        )

    def callout(self, title, text):
        self.ln(1)
        pad = 3
        self.set_font("Helvetica", "B", 10)
        title_lines = self.multi_cell(
            self.epw - 2 * pad, 5.2, title, dry_run=True, output="LINES"
        )
        self.set_font("Helvetica", "", 10)
        body_lines = self.multi_cell(
            self.epw - 2 * pad, 5.2, text, dry_run=True, output="LINES"
        )
        box_h = pad * 2 + 5.2 * (len(title_lines) + len(body_lines))
        x, y = self.get_x(), self.get_y()
        self.set_fill_color(*BOX_BG)
        self.set_draw_color(*BOX_BORDER)
        self.set_line_width(0.8)
        self.rect(x, y, self.epw, box_h, style="DF")
        self.set_xy(x + pad, y + pad)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*TEAL)
        self.multi_cell(
            self.epw - 2 * pad, 5.2, title, align="L", new_x="LMARGIN", new_y="NEXT"
        )
        self.set_x(x + pad)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*DARK)
        self.multi_cell(
            self.epw - 2 * pad, 5.2, text, align="L", new_x="LMARGIN", new_y="NEXT"
        )
        self.set_xy(x, y + box_h + 4)

    def numbered_step(self, n, title, body_text):
        self.ln(1)
        x, y = self.get_x(), self.get_y()
        d = 7
        self.set_fill_color(*BADGE_BG)
        self.ellipse(x, y, d, d, style="F")
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(255, 255, 255)
        self.set_xy(x, y + 0.9)
        self.cell(d, d - 1, str(n), align="C")
        self.set_xy(x + d + 3, y)
        self.set_font("Helvetica", "B", 11.5)
        self.set_text_color(*DARK)
        self.multi_cell(
            self.epw - d - 3, 6, title, align="L", new_x="LMARGIN", new_y="NEXT"
        )
        self.set_x(self.l_margin)
        self.ln(1)
        self.body(body_text)


def build():
    pdf = Recap(format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(20, 18, 20)

    # --- Page 1: title + big picture ---
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*DARK)
    pdf.cell(0, 12, "Product Adoption & Growth Analytics", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*GRAY)
    pdf.multi_cell(
        0, 6,
        "A plain-language recap of the project so far - written for someone new to "
        "machine learning",
        align="L", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.set_font("Helvetica", "I", 9.5)
    pdf.multi_cell(
        0, 5,
        "Prepared August 2026 - covers sessions from project kickoff through the "
        "end of Phase 1 (exploratory data analysis)",
        align="L", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(4)

    pdf.section_title("The Big Picture")
    pdf.body(
        "Imagine you work at a bank. The bank sells lots of different products: "
        "checking accounts, savings accounts, credit cards, mortgages, investment "
        "funds, and more. Most customers only use a handful of these products, "
        "even though some of them would genuinely benefit from a product they "
        "don't have yet."
    )
    pdf.body(
        "The bank can't realistically call, email, or advertise to every single "
        "customer about every single product every month - that's expensive, and "
        "it annoys people who get pitched things they'll never want. So the real "
        "business question is:"
    )
    pdf.set_font("Helvetica", "BI", 11)
    pdf.set_text_color(*TEAL)
    pdf.multi_cell(
        0, 6,
        '"Out of all our existing customers, who is actually likely to want a '
        'specific product next - and can we focus our limited marketing effort '
        'on them instead of everyone?"',
        align="L", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(2)
    pdf.body(
        "This project builds a system to answer that question for one specific "
        "product (a credit card), using real, anonymized data from a Spanish "
        'bank. In machine learning terms, this is called a "propensity model" - '
        "a model that estimates how likely someone is to do something (in this "
        "case, adopt a new product) based on what we already know about them."
    )
    pdf.callout(
        "Why this matters for learning ML:",
        "This kind of problem - ranking customers by likelihood of an action, "
        "with a limited budget to act on - shows up constantly in real jobs: "
        "who's likely to cancel their subscription (churn), who's likely to "
        "click an ad, who's likely to default on a loan. It's one of the most "
        "common, practical applications of machine learning in business.",
    )

    # --- Page 2: dataset ---
    pdf.add_page()
    pdf.section_title("The Dataset")
    pdf.body(
        "We're using a public dataset from Santander (a real bank), originally "
        "released for a Kaggle data science competition. A few key facts about it:"
    )
    pdf.bullet("About 13.6 million rows and roughly 950,000 unique customers.")
    pdf.bullet(
        '17 monthly "snapshots" of the bank\'s customers, from January 2015 to '
        "June 2016 - so the same customer appears multiple times, once per "
        "month, like a repeated survey."
    )
    pdf.bullet(
        "Each row records ~24 things about the customer (age, tenure with the "
        "bank, income, activity level, etc.) plus 24 yes/no flags for which "
        "products they currently hold."
    )
    pdf.ln(1)
    pdf.set_font("Helvetica", "B", 11.5)
    pdf.set_text_color(*DARK)
    pdf.cell(0, 7, "Why this dataset, specifically?", new_x="LMARGIN", new_y="NEXT")
    pdf.body(
        "It's real, messy data - not a cleaned-up textbook example. It has "
        "missing values, inconsistent categories, and customers who come and go, "
        "which is exactly what you'd deal with at a real job. It also happens to "
        "have the one structural feature this project absolutely needs: because "
        "it's the same customers tracked month after month, we can actually see "
        "when someone newly picks up a product - which is the whole basis for "
        "the prediction target."
    )
    pdf.callout(
        "Features vs. Label (two terms you'll see constantly in ML):",
        '"Features" are the inputs the model gets to look at (a customer\'s age, '
        'income, how many products they already have, etc.). The "label" is the '
        "correct answer we're trying to teach the model to predict (did this "
        "customer adopt a credit card next month: yes or no). Training a model "
        "is basically: show it lots of examples of features paired with the "
        "correct label, and let it find the statistical patterns that connect "
        "them.",
    )

    # --- Page 3+: steps ---
    pdf.add_page()
    pdf.section_title("What We've Actually Done, Step by Step")
    pdf.body(
        "Below is every real step taken so far, in order, explained in plain "
        'terms along with the reasoning behind it - not just "what" but "why."'
    )

    pdf.numbered_step(
        1,
        "Set up the project structure (before touching any data)",
        "Before writing any analysis code, we built a clean folder structure: "
        "separate places for raw data, processed data, code, reports, and "
        'documentation, plus a README and a roadmap. We also started a '
        '"decision log" - a folder where any significant choice gets written '
        "down with its reasoning.\n\n"
        "Why: this is the equivalent of drawing up a blueprint before building "
        "a house. On a real team, if everyone just writes code and notebooks "
        "with no structure, nobody (including future-you) can find anything or "
        "reconstruct why a decision was made. Writing decisions down as you "
        "make them is far easier and more honest than trying to remember your "
        "reasoning weeks later - and it's exactly what makes a project readable "
        "to someone else, like an interviewer.",
    )
    pdf.numbered_step(
        2,
        "Downloaded the data and verified it landed correctly",
        "Once the two data files were in place, we didn't just assume they "
        "were fine - we checked file sizes, counted rows, and confirmed the "
        "columns matched what was expected (48 columns: 24 profile columns + "
        "24 product flags).\n\n"
        'Why: this is a "trust but verify" habit. A corrupted download or a '
        "file that got cut off partway through is a common, boring failure "
        "that's very cheap to catch early and very annoying to catch after "
        "you've already built analysis on top of bad data.",
    )
    pdf.numbered_step(
        3,
        "Scanned the full file safely, without overloading the computer's memory",
        "The full data file is 2.29 GB on disk. Naively loading it entirely "
        "into memory with all 48 columns would have used roughly 15 GB of RAM "
        "- close enough to this computer's available memory to be risky. So "
        'instead of loading everything at once, the data was read in "chunks" '
        "of 500,000 rows at a time, tallying up statistics (like missing-value "
        "counts) as it went, and never holding more than one chunk in memory "
        "at once.",
    )
    pdf.callout(
        "Chunking, explained simply:",
        "Imagine trying to summarize a 1,000-page book, but you can only hold "
        "20 pages in your head at once. You'd read 20 pages, jot down notes, "
        "forget those pages, then read the next 20, and so on - adding to the "
        "same running notes the whole time. That's exactly what \"chunked "
        "reading\" does with a huge data file: process a manageable slice, "
        "keep a running tally, move on, and never need the whole book in your "
        "head simultaneously.",
    )
    pdf.body(
        "What we found: two columns were almost entirely empty (over 99.8% "
        'missing - not useful), the customer\'s income ("renta") was missing '
        "about 20.5% of the time (needs a thoughtful fix later, since income "
        "likely matters for who buys a credit card), and a cluster of "
        "unrelated-looking columns were all missing at exactly the same rate "
        "- a strong hint they're missing for the same underlying reason "
        "(probably brand-new customers whose very first monthly record is "
        "incomplete)."
    )

    pdf.add_page()
    pdf.numbered_step(
        4,
        'Picked which product to actually predict ("Service A")',
        "The dataset has 24 possible products we could try to predict "
        "adoption of. We had narrowed it to three realistic candidates: a "
        "credit card, a payroll account, or a mutual fund (investment "
        "product). We picked the credit card.",
    )
    pdf.set_font("Helvetica", "B", 10.5)
    pdf.set_text_color(*DARK)
    pdf.cell(0, 6, "Why credit card, specifically:", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(0.5)
    pdf.bullet(
        "Only about 3.7% to 5.8% of customers hold a credit card in any given "
        'month - meaning roughly 94-96% of customers are potential targets, '
        'which gives the model plenty of both "yes" and "no" examples to '
        "learn from."
    )
    pdf.bullet(
        "It's a product the bank can actually influence with marketing and "
        "outreach. A payroll account, by contrast, is mostly adopted because "
        "someone changed employers - something no amount of bank marketing "
        'can cause - which would have made the whole "targeting strategy" '
        "part of this project less meaningful."
    )
    pdf.bullet(
        "It's likely to correlate with a wide mix of other signals already in "
        "the data (activity level, income, how many other products someone "
        "has), giving the model more to actually learn from."
    )
    pdf.ln(1)
    pdf.body(
        "This reasoning, along with the real prevalence numbers behind it, "
        "was written up as a formal decision record in the project's docs "
        'folder - so if anyone (including us, months from now) wonders "why '
        'credit card and not investments?", the answer is documented, not '
        "just remembered."
    )

    pdf.numbered_step(
        5,
        'Built the "adoption label" - the actual target the model will learn to predict',
        "This is the most technically important step so far. For every "
        "customer, in every month, we needed to answer one specific question: "
        "did this customer NOT have a credit card last month, but DOES have "
        'one this month? If yes, that\'s an "adoption event" - the thing we '
        "eventually want a model to predict in advance.\n\n"
        'The naive way to do this in code is to sort each customer\'s rows by '
        'month and just grab "the previous row." But that\'s a subtle trap: '
        "about 7.1% of customer-month records don't have a record from "
        "exactly one month before (because that customer joined partway "
        "through, or had a gap where they temporarily left the bank's radar). "
        'If you just grab "the previous row" positionally, you might '
        "accidentally compare March to January and think it's "
        "March-vs-February - silently producing a wrong answer with no error "
        "message.\n\n"
        "To avoid that, each row was matched to its true previous month using "
        "an exact date-based match (customer ID + calendar month), and any "
        'row where no true "last month" record existed was explicitly marked '
        "as unknown, rather than guessed at.",
    )
    pdf.callout(
        "The single most important finding from this step:",
        "Only about 0.57% of eligible customer-months resulted in an actual "
        "adoption event (69,118 adoptions out of about 12.1 million eligible "
        "customer-months). In other words, adopting a credit card in any "
        "given month is rare - roughly 1 in every 175 eligible customers.",
    )
    pdf.body(
        'Why this matters a lot for what comes next: imagine a lazy model '
        'that just always predicts "no, this customer will not adopt a '
        "credit card.\" That model would be right 99.43% of the time - and "
        "completely useless, since it never identifies anyone to target. "
        'This is called "class imbalance," and it\'s exactly why the '
        'project\'s success metric was chosen up front to be "precision at '
        'K" (out of the top K customers the model ranks as most likely, how '
        "many actually adopt?) rather than plain accuracy. A rare-event "
        "problem needs a ranking-based grading system, not a simple "
        "right/wrong percentage."
    )

    # --- Step 6: EDA ---
    pdf.add_page()
    pdf.numbered_step(
        6,
        "Looked for patterns: does adoption change over time, or by who the customer is?",
        "With the label in hand, the next step was exploratory data analysis "
        "(EDA) - looking at the data to find patterns, before building any "
        "predictive model. Two questions: does the adoption rate change over "
        "the 17-month window, and does it differ by customer characteristics "
        "like age, how long they've been a customer, income, or how active "
        "they are?",
    )
    pdf.callout(
        "A subtlety worth calling out: using \"before\" information, not \"after\":",
        "To compare adoption rates by, say, income, you need to know each "
        "customer's income. The tempting shortcut is to use their income from "
        "the same month they adopted the card - but that's information from "
        "*after* the fact, and a customer's profile can shift slightly around "
        "the time they pick up a new product. So instead, every comparison "
        "below uses each customer's information from the month *before* they "
        "could have adopted - the same information a real targeting decision "
        "would actually have access to. Using \"after the fact\" information "
        "by mistake is called \"leakage,\" and it's one of the most common "
        "ways a model ends up looking far more accurate in testing than it "
        "will ever be in real use.",
    )
    pdf.body(
        "What we found, in plain terms:"
    )
    pdf.bullet(
        "Over time: the monthly adoption rate roughly halved across the "
        "17-month window, from around 0.8% in mid-2015 down to around 0.45% "
        "by early-mid 2016, with no strong seasonal pattern."
    )
    pdf.bullet(
        "Whether a customer is currently \"active\" with the bank "
        "(the activity index) was the single biggest differentiator found: "
        "active customers adopted at about 50 times the rate of inactive "
        "ones (1.28% vs. 0.03%)."
    )
    pdf.bullet(
        "The bank's own customer segment label (a VIP-style \"TOP\" tier vs. "
        "regular retail customers vs. students) showed a more than 30x "
        "spread - the TOP segment adopted at about 3.0%, versus roughly 0.1% "
        "for students."
    )
    pdf.bullet(
        "How long someone has been a customer (tenure) mattered a lot too: "
        "adoption climbed steadily from about 0.1% for customers with under "
        "6 months' history to about 1.4% for customers of 20+ years - a "
        "roughly 13x spread, and a clean, steady relationship rather than a "
        "noisy one."
    )
    pdf.bullet(
        "Income and age also mattered, but more modestly: higher-income "
        "customers adopted at roughly 2.4 times the rate of lower-income "
        "ones, and adoption rose with age up to the 40-50 bracket before "
        "declining again for older customers."
    )
    pdf.body(
        "Along the way, a few data-quality quirks were also flagged for "
        "later cleanup: a small number of rows have an obviously-wrong "
        "placeholder value for tenure, and some ages in the raw data are "
        "implausible (over 160 years old) - both need explicit handling "
        "before they're used to train a model, rather than being silently "
        "ignored the way this exploratory pass did."
    )
    pdf.callout(
        "Why this step matters for what comes next:",
        "This is the step where you start to see, in plain terms, which "
        "pieces of information are worth giving a model. Activity level, "
        "tenure, and customer segment all look like strong candidates for "
        "the first real predictive model in Phase 2; income and age look "
        "like real but secondary signals. Full numbers are written up in "
        "reports/01_eda_findings.md and the underlying notebook.",
    )

    # --- Final page: status + next ---
    pdf.add_page()
    pdf.section_title("Where We Are Now, and What's Next")
    pdf.body(
        "Every step above is committed to the project's version control "
        "history (git), with a written explanation attached to each commit, "
        "and the repository is live on GitHub. At this point:"
    )
    pdf.bullet("The problem is defined: predict which existing customers will newly adopt a credit card.")
    pdf.bullet("The dataset is verified, understood, and its data-quality issues are documented.")
    pdf.bullet('The prediction target ("Service A") is decided and justified with real numbers.')
    pdf.bullet(
        "The label - the actual right-answer column the model will eventually "
        "be trained on - exists as a processed data file, built carefully to "
        "avoid a subtle but easy-to-miss bug."
    )
    pdf.bullet(
        "The exploratory analysis is done: adoption rate over time and by "
        "customer segment, with activity level, tenure, and customer segment "
        "standing out as the strongest patterns found so far."
    )
    pdf.ln(1)
    pdf.set_font("Helvetica", "B", 11.5)
    pdf.set_text_color(*TEAL)
    pdf.cell(0, 7, "Phase 1 is complete.", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*TEAL)
    pdf.cell(0, 7, "Next up", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    pdf.body(
        "Phase 2: build the first real predictive model. This starts with "
        "splitting the data by time (train on earlier months, test on later "
        "ones - not a random split, since randomly mixing months would let "
        "the model implicitly \"see the future\" during training), then "
        "engineering features informed by this session's findings (tenure, "
        "activity level, and customer segment first), then training a "
        "baseline model and a stronger one (logistic regression and "
        "LightGBM) to compare against."
    )
    pdf.body(
        "After that: explaining what drives the model's predictions in plain "
        "English (Phase 3), and turning it into an actual targeting "
        "recommendation with a rough cost/benefit estimate (Phase 4)."
    )
    pdf.set_font("Helvetica", "I", 9.5)
    pdf.set_text_color(*GRAY)
    pdf.multi_cell(
        0, 5,
        "A note on honesty about limitations: this is Spanish retail banking "
        "data from 2015-2016, so none of the specific numbers here (adoption "
        "rates, etc.) would transfer directly to a different bank or a "
        "different time period. The point of this project is to demonstrate "
        "the methodology - how to responsibly go from a business question to "
        "a data-backed targeting recommendation - not to claim these exact "
        "figures apply anywhere else.",
    )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(OUT_PATH))
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    build()
