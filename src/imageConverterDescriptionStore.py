"""Persist explicit GUI corrections for an exact catalog image, not its family."""
from __future__ import annotations

from pathlib import Path
import re
import threading
import time
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape, quoteattr

from src.imageConverterRecognition import pixel_digest, rgb_image


_WRITE_LOCK = threading.RLock()


class DescriptionStore:
    def __init__(self, root):
        self.root = Path(root).resolve()

    def save(self, name, source_sha256, description):
        """Keep XML layout, sibling variants and the family description intact."""
        result = dict(scope='image', message='Beschreibung für dieses Bild gespeichert.')
        if not description.strip() or Path(name).name != name:
            return result
        original = (self.root/'artifacts/images_to_convert'/name).resolve()
        if not original.is_relative_to(self.root) or not original.is_file():
            return result
        if pixel_digest(rgb_image(original)) != source_sha256:
            return dict(result, message='Beschreibung für dieses Bild gespeichert; abweichendes Katalogoriginal bleibt unverändert.')
        with _WRITE_LOCK:
            paths = [self.root/'artifacts'/folder/'Finale_Wurzelformen_V3.xml'
                     for folder in ('images_to_convert', 'descriptions')]
            files = []
            for path in paths:
                if not path.is_file():
                    continue
                data = path.read_bytes()
                text = data.decode('utf-8-sig')
                tree = ET.fromstring(text)
                names = {(node.text or '').strip() for node in tree.findall('.//bilder/bild')
                         if (node.text or '').strip().casefold() == name.casefold()}
                if not names:
                    continue
                count = 0
                def replace(match):
                    nonlocal count
                    if match['name'].strip() not in {escape(value) for value in names}:
                        return match[0]
                    attrs = re.sub(r'\s+beschreibung(?:_modus)?\s*=\s*(?:"[^"]*"|\x27[^\x27]*\x27)', '', match['attrs'])
                    count += 1
                    # Character references preserve intentional newlines in attributes.
                    quoted = quoteattr(description).replace('\n', '&#10;').replace('\r', '&#13;').replace('\t', '&#9;')
                    return f'<bild{attrs} beschreibung={quoted} beschreibung_modus="ersetzen">{match["name"]}</bild>'
                updated = re.sub(r'<bild\b(?P<attrs>[^>]*)>(?P<name>[^<]*)</bild>', replace, text)
                if not count:
                    continue
                ET.fromstring(updated)  # Never publish a malformed maintained table.
                if updated != text:
                    temporary = path.with_suffix('.xml.tmp')
                    temporary.write_bytes(updated.encode('utf-8'))
                    for attempt in range(6):
                        try:
                            temporary.replace(path)
                            break
                        except PermissionError:
                            if attempt == 5:
                                raise
                            time.sleep(.02*2**attempt)
                files.append(path.relative_to(self.root).as_posix())
            if files:
                result.update(scope='catalog', files=files,
                              message='Beschreibung gespeichert und für dieses Katalogbild übernommen.')
            return result

    def recover(self, jobs):
        """Recover recent submitted corrections newer than the maintained table.

        Old experiments must not replace later maintained XML corrections.
        Only the latest explicit user text per filename is considered.
        """
        primary = self.root/'artifacts/images_to_convert/Finale_Wurzelformen_V3.xml'
        if not primary.is_file():
            return []
        cutoff = primary.stat().st_mtime
        seen, recovered = set(), []
        for job in sorted(jobs, key=lambda job: job.get('description_saved_at', job.get('started', job.get('created', 0))), reverse=True):
            if job.get('description_origin') != 'user' or job['name'].casefold() in seen:
                continue
            seen.add(job['name'].casefold())
            if job.get('description_saved_at', job.get('started', job.get('created', 0))) <= cutoff:
                continue
            result = self.save(job['name'], job.get('source_sha256'), job.get('description', ''))
            if result['scope'] == 'catalog':
                recovered.append(dict(filename=job['name'], job_id=job['id'], **result))
        return recovered
