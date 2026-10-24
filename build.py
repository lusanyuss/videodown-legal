import html
import json
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit

root = Path(__file__).resolve().parent
data = json.loads((root / 'content.json').read_text(encoding='utf-8'))
out = root / 'dist'
out.mkdir(exist_ok=True)
esc = html.escape
ids = ('privacy', 'terms', 'deletion', 'support')
for lang, text in data['languages'].items():
    for page in ('index', *ids):
        hub = page == 'index'
        base = '../' if hub else '../../'
        title = text['hub'] if hub else text['documents'][page]['title']
        local = lambda name: f'{name}/' if hub else f'../{name}/'
        nav = ''.join(f'<a href="{local(name)}"'+(' aria-current="page"' if name == page else '')+f'>{esc(text["documents"][name]["title"])}</a>' for name in ids)
        body = ''.join(f'<section><h2><a href="{local(name)}">{esc(text["documents"][name]["title"])}</a></h2><p>{esc(text["documents"][name]["summary"])}</p></section>' for name in ids) if hub else ''.join(f'<section><h2>{esc(section["title"])}</h2>'+''.join(f'<p>{esc(p)}</p>' for p in section['paragraphs'])+'</section>' for section in text['documents'][page]['sections'])
        other = 'zh' if lang == 'en' else 'en'
        destination = out / lang / ('' if hub else page) / 'index.html'
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(f"""<!doctype html>
<html lang="{'zh-CN' if lang == 'zh' else 'en'}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="referrer" content="no-referrer"><meta http-equiv="Content-Security-Policy" content="default-src 'self'; style-src 'self'; script-src 'none'; connect-src 'none'; base-uri 'none'; form-action 'none'"><title>{esc(title)} · {esc(text['name'])}</title><meta name="description" content="{esc(text['intro'])}"><link rel="stylesheet" href="{base}styles.css"></head><body><a class="skip" href="#main">{'跳到正文' if lang == 'zh' else 'Skip to content'}</a><header><a class="brand" href="{'./' if hub else '../'}">{esc(text['name'])}</a><a href="{base}{other}/{'' if hub else page + '/'}" lang="{other}">{'English' if lang == 'zh' else '简体中文'}</a></header><main id="main"><nav aria-label="{'协议导航' if lang == 'zh' else 'Document navigation'}">{nav}</nav><h1>{esc(title)}</h1><p class="intro">{esc(text['intro'])}</p><p class="meta">{'生效及更新日期：2026年10月25日' if lang == 'zh' else 'Effective and updated: October 25, 2026'}</p>{body}<aside><strong>{'服务提供者' if lang == 'zh' else 'Service provider'}: {esc(data['operator'])}</strong><p>{'联系邮箱' if lang == 'zh' else 'Contact'}: <a href="mailto:{esc(data['email'])}">{esc(data['email'])}</a></p><p>{'邮件由你主动发送；不要提供密码、验证码或完整付款资料。' if lang == 'zh' else 'You choose whether to send email. Do not include passwords, verification codes or full payment details.'}</p></aside></main><footer>{esc(text['name'])} · {'隐私与支持' if lang == 'zh' else 'Privacy & support'}</footer></body></html>""", encoding='utf-8')
root_html = (out / 'en/index.html').read_text(encoding='utf-8').replace('href="../styles.css"', 'href="styles.css"').replace('href="../zh/"', 'href="zh/"').replace('href="./"', 'href="en/"')
for name in ids:
    root_html = root_html.replace(f'href="{name}/"', f'href="en/{name}/"')
(out / 'index.html').write_text(root_html, encoding='utf-8')
(out / 'styles.css').write_bytes((root / 'styles.css').read_bytes())
(out / '.nojekyll').write_text('', encoding='utf-8')

class Links(HTMLParser):
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        assert tag not in ('script', 'iframe', 'form'), tag
        for key in ('href', 'src'):
            if key not in attrs:
                continue
            value = attrs[key]
            parsed = urlsplit(value)
            if parsed.scheme:
                assert parsed.scheme in ('https', 'mailto'), value
            elif parsed.path:
                target = (self.file.parent / parsed.path).resolve()
                assert target.is_relative_to(out.resolve()), value
                assert (target / 'index.html' if target.is_dir() else target).is_file(), value
pages = list(out.rglob('*.html'))
assert len(pages) == 11, len(pages)
for file in pages:
    body = file.read_text(encoding='utf-8')
    assert data['operator'] in body and data['email'] in body
    checker = Links()
    checker.file = file
    checker.feed(body)
print('Built and checked 11 bilingual pages, local links, provider and contact; no scripts or forms.')
