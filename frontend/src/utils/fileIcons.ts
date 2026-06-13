/** 根据文件后缀返回图标颜色和标签 */
export function getFileIcon(name: string, isDir: boolean): { color: string; label: string } {
  if (isDir) return { color: '#E6A23C', label: '' }
  const ext = name.includes('.') ? name.split('.').pop()!.toLowerCase() : ''
  const map: Record<string, { color: string; label: string }> = {
    // 图片
    jpg: { color: '#e91e8c', label: 'JPG' }, jpeg: { color: '#e91e8c', label: 'JPG' },
    png: { color: '#e91e8c', label: 'PNG' }, gif: { color: '#e91e8c', label: 'GIF' },
    svg: { color: '#e91e8c', label: 'SVG' }, webp: { color: '#e91e8c', label: 'WEBP' },
    bmp: { color: '#e91e8c', label: 'BMP' }, ico: { color: '#e91e8c', label: 'ICO' },
    psd: { color: '#e91e8c', label: 'PSD' }, ai: { color: '#e91e8c', label: 'AI' },
    // 视频
    mp4: { color: '#f56c6c', label: 'MP4' }, avi: { color: '#f56c6c', label: 'AVI' },
    mkv: { color: '#f56c6c', label: 'MKV' }, mov: { color: '#f56c6c', label: 'MOV' },
    wmv: { color: '#f56c6c', label: 'WMV' }, flv: { color: '#f56c6c', label: 'FLV' },
    webm: { color: '#f56c6c', label: 'WEBM' }, mts: { color: '#f56c6c', label: 'MTS' },
    // 音频
    mp3: { color: '#ff9500', label: 'MP3' }, wav: { color: '#ff9500', label: 'WAV' },
    flac: { color: '#ff9500', label: 'FLAC' }, aac: { color: '#ff9500', label: 'AAC' },
    ogg: { color: '#ff9500', label: 'OGG' }, wma: { color: '#ff9500', label: 'WMA' },
    m4a: { color: '#ff9500', label: 'M4A' },
    // 文档
    doc: { color: '#2b7cd3', label: 'DOC' }, docx: { color: '#2b7cd3', label: 'DOC' },
    txt: { color: '#909399', label: 'TXT' }, rtf: { color: '#2b7cd3', label: 'RTF' },
    odt: { color: '#2b7cd3', label: 'ODT' }, md: { color: '#909399', label: 'MD' },
    // 表格
    xls: { color: '#217346', label: 'XLS' }, xlsx: { color: '#217346', label: 'XLS' },
    csv: { color: '#217346', label: 'CSV' },
    // 演示
    ppt: { color: '#d04423', label: 'PPT' }, pptx: { color: '#d04423', label: 'PPT' },
    // PDF
    pdf: { color: '#e53935', label: 'PDF' },
    // 压缩
    zip: { color: '#ffc107', label: 'ZIP' }, rar: { color: '#ffc107', label: 'RAR' },
    '7z': { color: '#ffc107', label: '7Z' }, tar: { color: '#ffc107', label: 'TAR' },
    gz: { color: '#ffc107', label: 'GZ' }, bz2: { color: '#ffc107', label: 'BZ2' },
    xz: { color: '#ffc107', label: 'XZ' }, zst: { color: '#ffc107', label: 'ZST' },
    // 代码
    js: { color: '#f7df1e', label: 'JS' }, ts: { color: '#3178c6', label: 'TS' },
    jsx: { color: '#61dafb', label: 'JSX' }, tsx: { color: '#3178c6', label: 'TSX' },
    py: { color: '#3776ab', label: 'PY' }, java: { color: '#ed8b00', label: 'JAVA' },
    c: { color: '#555555', label: 'C' }, cpp: { color: '#555555', label: 'C++' },
    h: { color: '#555555', label: 'H' }, cs: { color: '#239120', label: 'C#' },
    go: { color: '#00add8', label: 'GO' }, rs: { color: '#dea584', label: 'RS' },
    rb: { color: '#cc342d', label: 'RB' }, php: { color: '#777bb4', label: 'PHP' },
    swift: { color: '#fa7343', label: 'SWIFT' }, kt: { color: '#7f52ff', label: 'KT' },
    html: { color: '#e34c26', label: 'HTML' }, htm: { color: '#e34c26', label: 'HTM' },
    css: { color: '#264de4', label: 'CSS' }, scss: { color: '#cc6699', label: 'SCSS' },
    less: { color: '#1d365d', label: 'LESS' },
    json: { color: '#292929', label: 'JSON' }, xml: { color: '#f06529', label: 'XML' },
    yaml: { color: '#cb171e', label: 'YAML' }, yml: { color: '#cb171e', label: 'YML' },
    toml: { color: '#9c4221', label: 'TOML' }, ini: { color: '#909399', label: 'INI' },
    sh: { color: '#4eaa25', label: 'SH' }, bash: { color: '#4eaa25', label: 'SH' },
    zsh: { color: '#4eaa25', label: 'ZSH' }, bat: { color: '#4eaa25', label: 'BAT' },
    ps1: { color: '#012456', label: 'PS1' },
    sql: { color: '#e38c00', label: 'SQL' },
    vue: { color: '#42b883', label: 'VUE' }, svelte: { color: '#ff3e00', label: 'SVELTE' },
    // 可执行 / 安装
    exe: { color: '#67c23a', label: 'EXE' }, msi: { color: '#67c23a', label: 'MSI' },
    dmg: { color: '#67c23a', label: 'DMG' }, app: { color: '#67c23a', label: 'APP' },
    deb: { color: '#67c23a', label: 'DEB' }, rpm: { color: '#67c23a', label: 'RPM' },
    apk: { color: '#67c23a', label: 'APK' }, jar: { color: '#67c23a', label: 'JAR' },
    // 字体
    ttf: { color: '#606266', label: 'TTF' }, otf: { color: '#606266', label: 'OTF' },
    woff: { color: '#606266', label: 'WOFF' }, woff2: { color: '#606266', label: 'WOFF2' },
    eot: { color: '#606266', label: 'EOT' },
    // 数据 / 配置
    db: { color: '#909399', label: 'DB' }, sqlite: { color: '#909399', label: 'DB' },
    log: { color: '#909399', label: 'LOG' }, env: { color: '#909399', label: 'ENV' },
    // 镜像
    iso: { color: '#606266', label: 'ISO' }, img: { color: '#606266', label: 'IMG' },
    vmdk: { color: '#606266', label: 'VMDK' },
  }
  if (map[ext]) return map[ext]
  return { color: '#409EFF', label: ext.toUpperCase().slice(0, 4) || '?' }
}
