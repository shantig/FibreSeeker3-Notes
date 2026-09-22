#!/bin/sh
set -eu

if [ "$#" -lt 3 ] || [ "$#" -gt 4 ]; then
  echo "usage: $0 RECORD_ID URL FILENAME [PROVENANCE_CLASS]" >&2
  exit 64
fi

record_id=$1
source_url=$2
filename=$3
provenance_class=${4:-FIBRESEEK_OFFICIAL}
archive_root=${FIBRESEEK_ARCHIVE_ROOT:-<archive>/FibreSeeker-KB-Archive}
record_dir="$archive_root/originals/$provenance_class/$record_id"
destination="$record_dir/$filename"
headers="$record_dir/response-headers.txt"
metadata="$record_dir/retrieval.txt"
temporary="$destination.partial"
tls_option=

if [ "${ALLOW_EXPIRED_TLS:-0}" = "1" ]; then
  tls_option=--insecure
fi

if [ ! -d "$archive_root" ]; then
  echo "archive root is unavailable: $archive_root" >&2
  exit 1
fi

if [ -e "$record_dir" ]; then
  if [ -f "$destination" ] && [ -f "$metadata" ] &&
     grep -Fqx "source_url=$source_url" "$metadata" &&
     grep -Fqx "filename=$filename" "$metadata"; then
    recorded_sha=$(sed -n 's/^sha256=//p' "$metadata" | tail -n 1)
    current_sha=$(shasum -a 256 "$destination" | awk '{print $1}')
    if [ -n "$recorded_sha" ] && [ "$recorded_sha" = "$current_sha" ]; then
      echo "already acquired and byte-identical: $destination"
      exit 0
    fi
  fi
  echo "refusing to overwrite non-identical existing record: $record_dir" >&2
  exit 1
fi

mkdir -p "$record_dir"
trap 'rm -f "$temporary"' EXIT HUP INT TERM

curl $tls_option --fail --location --silent --show-error \
  --user-agent "FibreSeeker-KB-Archivist/1.0 (polite preservation; contact project owner)" \
  --dump-header "$headers" \
  --output "$temporary" \
  --write-out 'source_url=%{url}\nfinal_url=%{url_effective}\nhttp_code=%{http_code}\ncontent_type=%{content_type}\nsize_download=%{size_download}\n' \
  "$source_url" > "$metadata"

mv "$temporary" "$destination"
{
  printf 'retrieved_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf 'filename=%s\n' "$filename"
  printf 'byte_size=%s\n' "$(stat -f %z "$destination")"
  printf 'sha256=%s\n' "$(shasum -a 256 "$destination" | awk '{print $1}')"
  printf 'detected_mime=%s\n' "$(file -b --mime-type "$destination")"
  printf 'tls_verification=%s\n' "$(if [ -n "$tls_option" ]; then printf disabled; else printf enabled; fi)"
} >> "$metadata"

sleep 2
