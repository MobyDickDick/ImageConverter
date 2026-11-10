"""The saved report must expose its records even when scripts never execute."""
from html.parser import HTMLParser
import json
from pathlib import Path

from tools.build_catalog_inventory import build, write_report
from tests.test_catalog_inventory import prepare, quality


class StaticInventory(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.in_body = False
        self.rows = []
        self.current = None
        self.sort_buttons_disabled = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'tbody' and attrs.get('id') == 'body':
            self.in_body = True
        if self.in_body and tag == 'tr':
            self.current = dict(text=[], links=[], images=[])
        if self.current is not None:
            if tag == 'a':
                self.current['links'].append(attrs.get('href'))
            if tag == 'img':
                self.current['images'].append(attrs.get('src'))
        if tag == 'button' and attrs.get('class') == 'column-sort':
            self.sort_buttons_disabled.append('disabled' in attrs)

    def handle_endtag(self, tag):
        if tag == 'tr' and self.current is not None:
            self.rows.append(self.current)
            self.current = None
        if tag == 'tbody':
            self.in_body = False

    def handle_data(self, text):
        if self.current is not None:
            self.current['text'].append(text)


def report(tmp_path, **options):
    prepare(tmp_path, **options)
    rows, summary, _ = build(tmp_path, measure=lambda *args: quality())
    output = tmp_path/'report'
    write_report(tmp_path, output, rows, summary, {})
    html = (output/'index.html').read_text(encoding='utf-8')
    return html, StaticInventory(html), output


def test_rows_and_links_exist_in_html_without_executing_javascript(tmp_path):
    html, parsed, _ = report(tmp_path, archived=True)
    assert len(parsed.rows) == 1
    text = ' '.join(parsed.rows[0]['text'])
    assert 'AA0010.jpg' in text and 'Graues Rechteck.' in text
    assert 'Historisch archiviert' in text and 'Rastergates erfüllt' in text
    assert any(link.endswith('.svg') for link in parsed.rows[0]['links'])
    assert len(parsed.rows[0]['images']) == 1
    assert parsed.sort_buttons_disabled == [True]*5
    assert 'auch ohne JavaScript sichtbar' in html
    assert 'class="cards"><div class="card"><strong>1</strong>' in html


def test_static_text_is_escaped_and_marker_text_is_preserved(tmp_path):
    description = '</td><script>alert("x")</script> __CATALOG_ROWS__'
    html, parsed, _ = report(tmp_path, desc=description)
    assert len(parsed.rows) == 1
    assert description in ''.join(parsed.rows[0]['text'])
    assert '</td><script>alert' not in html
    assert '\\u003c/script' in html


def test_reserved_records_remain_visible_without_loading_a_thumbnail(tmp_path):
    html, parsed, _ = report(tmp_path, reserved=True)
    assert len(parsed.rows) == 1
    assert not parsed.rows[0]['images']
    assert 'Reserviert, nicht geprüft' in ' '.join(parsed.rows[0]['text'])
    assert 'Messung gesperrt' in html


def test_every_record_is_saved_even_above_the_default_page_limit(tmp_path):
    prepare(tmp_path)
    rows, summary, _ = build(tmp_path, measure=lambda *args: quality())
    rows = [dict(rows[0], filename=f'bitmap_{index:03d}.jpg') for index in range(160)]
    output = tmp_path/'report'
    write_report(tmp_path, output, rows, summary, {})
    parsed = StaticInventory((output/'index.html').read_text(encoding='utf-8'))
    assert len(parsed.rows) == 160
    assert 'bitmap_159.jpg' in ''.join(parsed.rows[-1]['text'])
    assert len(json.loads((output/'manifest.json').read_text(encoding='utf-8'))['rows']) == 160


def test_raw_template_links_to_real_report_and_generated_report_has_no_template_notice(tmp_path):
    template_path = Path(__file__).resolve().parents[1]/'tools/templates/catalog_inventory.html'
    template = template_path.read_text(encoding='utf-8')
    assert 'Dies ist die HTML-Vorlage' in template
    assert '../../artifacts/catalog_inventory/index.html' in template
    html, parsed, _ = report(tmp_path)
    assert 'Dies ist die HTML-Vorlage' not in html
    assert '__CATALOG_' not in html
    assert len(parsed.rows) == 1
