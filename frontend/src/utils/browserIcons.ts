/** 解析 user_agent 返回浏览器名称和颜色 */
export function parseBrowser(ua: string): { name: string; color: string; key: string } {
  if (!ua) return { name: '未知', color: '#909399', key: 'unknown' }
  
  const s = ua.toLowerCase()
  
  // 微信内置浏览器
  if (s.includes('micromessenger')) return { name: '微信', color: '#07C160', key: 'wechat' }
  // 钉钉
  if (s.includes('dingtalk')) return { name: '钉钉', color: '#0089FF', key: 'dingtalk' }
  // 企业微信
  if (s.includes('wxwork')) return { name: '企微', color: '#07C160', key: 'wechat' }
  // QQ浏览器
  if (s.includes('qqbrowser')) return { name: 'QQ', color: '#12B7F5', key: 'qq' }
  // 抖音
  if (s.includes('bytedancewebview') || s.includes('ttwebview')) return { name: '抖音', color: '#161823', key: 'douyin' }
  // Edge (必须在 Chrome 之前)
  if (s.includes('edg/') || s.includes('edge/')) return { name: 'Edge', color: '#0078D7', key: 'edge' }
  // Opera
  if (s.includes('opr/') || s.includes('opera')) return { name: 'Opera', color: '#FF1B2D', key: 'opera' }
  // Vivaldi
  if (s.includes('vivaldi')) return { name: 'Vivaldi', color: '#EF3939', key: 'vivaldi' }
  // Yandex
  if (s.includes('yabrowser')) return { name: 'Yandex', color: '#FF0000', key: 'yandex' }
  // Samsung
  if (s.includes('samsungbrowser')) return { name: 'Samsung', color: '#1428A0', key: 'samsung' }
  // UC浏览器
  if (s.includes('ucbrowser') || s.includes('ucweb')) return { name: 'UC', color: '#FF6A00', key: 'uc' }
  // 搜狗
  if (s.includes('metasr') || s.includes('se 2.x')) return { name: '搜狗', color: '#FF6A00', key: 'sogou' }
  // 360
  if (s.includes('qihoo') || s.includes('360se') || s.includes('360ee')) return { name: '360', color: '#1DBF1D', key: '360' }
  // 猎豹
  if (s.includes('lbbrowser')) return { name: '猎豹', color: '#27C24C', key: 'cheetah' }
  // 夸克
  if (s.includes('quark')) return { name: '夸克', color: '#6A5ACD', key: 'quark' }
  // Firefox
  if (s.includes('firefox')) return { name: 'Firefox', color: '#FF7139', key: 'firefox' }
  // Safari (必须在 Chrome 之后，因为 Chrome UA 也包含 Safari)
  if (s.includes('safari/') && !s.includes('chrome')) return { name: 'Safari', color: '#006CFF', key: 'safari' }
  // Chrome (放在最后，因为很多浏览器 UA 都包含 Chrome)
  if (s.includes('chrome/') && !s.includes('edg')) return { name: 'Chrome', color: '#4285F4', key: 'chrome' }
  // IE
  if (s.includes('msie') || s.includes('trident/')) return { name: 'IE', color: '#0078D7', key: 'ie' }
  // Android WebView
  if (s.includes('android') && !s.includes('chrome')) return { name: 'Android', color: '#3DDC84', key: 'android' }
  
  return { name: '其他', color: '#909399', key: 'other' }
}
