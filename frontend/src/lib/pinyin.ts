/**
 * 简易拼音搜索工具
 * 支持：
 * 1. 拼音全拼匹配（如 "dakai" 匹配 "打开"）
 * 2. 拼音首字母匹配（如 "dk" 匹配 "打开"）
 * 3. 混合匹配（如 "da开" 匹配 "打开"）
 */

// 常用汉字拼音映射表
const pinyinMap: Record<string, string> = {
  // 模块相关常用字
  打: 'da', 开: 'kai', 网: 'wang', 页: 'ye', 点: 'dian', 击: 'ji',
  元: 'yuan', 素: 'su', 悬: 'xuan', 停: 'ting', 输: 'shu', 入: 'ru',
  文: 'wen', 本: 'ben', 提: 'ti', 取: 'qu', 数: 'shu', 据: 'ju',
  等: 'deng', 待: 'dai', 固: 'gu', 定: 'ding', 关: 'guan', 闭: 'bi',
  刷: 'shua', 新: 'xin', 后: 'hou', 退: 'tui', 前: 'qian', 进: 'jin',
  设: 'she', 置: 'zhi', 变: 'bian', 量: 'liang', 印: 'yin',
  日: 'ri', 志: 'zhi', 播: 'bo', 放: 'fang', 示: 'shi',
  音: 'yin', 乐: 'yue', 弹: 'tan', 窗: 'chuang', 朗: 'lang', 读: 'du',
  脚: 'jiao', 分: 'fen', 组: 'zu', 备: 'bei', 注: 'zhu', 下: 'xia',
  拉: 'la', 框: 'kuang', 选: 'xuan', 择: 'ze', 复: 'fu', 勾: 'gou',
  拖: 'tuo', 拽: 'zhuai', 滚: 'gun', 动: 'dong', 上: 'shang', 传: 'chuan',
  件: 'jian', 载: 'zai', 保: 'bao', 存: 'cun', 图: 'tu',
  片: 'pian', 截: 'jie', 验: 'yan', 证: 'zheng', 码: 'ma', 识: 'shi',
  别: 'bie', 滑: 'hua', 块: 'kuai', 发: 'fa', 送: 'song', 邮: 'you',
  剪: 'jian', 贴: 'tie', 板: 'ban', 获: 'huo', 键: 'jian', 盘: 'pan',
  操: 'cao', 作: 'zuo', 真: 'zhen', 实: 'shi', 鼠: 'shu', 标: 'biao',
  机: 'ji', 重: 'zhong', 启: 'qi', 锁: 'suo', 屏: 'ping', 幕: 'mu',
  移: 'yi', 执: 'zhi', 行: 'xing', 命: 'ming', 令: 'ling', 像: 'xiang',
  位: 'wei', 条: 'tiao', 判: 'pan', 断: 'duan', 循: 'xun',
  环: 'huan', 遍: 'bian', 历: 'li', 计: 'ji', 划: 'hua', 任: 'ren',
  务: 'wu', 调: 'tiao', 用: 'yong', 子: 'zi', 流: 'liu', 程: 'cheng',
  结: 'jie', 束: 'shu', 跳: 'tiao', 过: 'guo', 正: 'zheng', 则: 'ze',
  表: 'biao', 达: 'da', 式: 'shi', 替: 'ti', 换: 'huan',
  割: 'ge', 合: 'he', 并: 'bing', 拼: 'pin', 接: 'jie', 去: 'qu',
  空: 'kong', 格: 'ge', 大: 'da', 小: 'xiao', 写: 'xie', 转: 'zhuan',
  解: 'jie', 析: 'xi', 编: 'bian', 随: 'sui', 时: 'shi', 间: 'jian',
  列: 'lie', 添: 'tian', 加: 'jia', 删: 'shan', 除: 'chu', 长: 'chang',
  度: 'du', 字: 'zi', 典: 'dian', 值: 'zhi', 所: 'suo', 有: 'you',
  单: 'dan', 清: 'qing', 导: 'dao', 出: 'chu', 连: 'lian', 查: 'cha',
  询: 'xun', 插: 'cha', 更: 'geng', 智: 'zhi', 能: 'neng', 对: 'dui',
  话: 'hua', 视: 'shi', 觉: 'jue', 请: 'qing', 求: 'qiu', 抓: 'zhua',
  包: 'bao', 络: 'luo', 处: 'chu', 理: 'li', 模: 'mo',
  搜: 'sou', 索: 'suo', 配: 'pei', 基: 'ji', 础: 'chu', 高: 'gao',
  级: 'ji', 控: 'kong', 制: 'zhi', 系: 'xi', 统: 'tong', 库: 'ku',
  人: 'ren', 工: 'gong', 名: 'ming', 称: 'cheng', 内: 'nei', 容: 'rong',
  信: 'xin', 息: 'xi', 属: 'shu', 性: 'xing', 链: 'lian', 地: 'di',
  址: 'zhi', 资: 'zi', 源: 'yuan', 路: 'lu', 径: 'jing', 目: 'mu',
  录: 'lu', 类: 'lei', 型: 'xing', 状: 'zhuang', 态: 'tai', 功: 'gong',
  方: 'fang', 法: 'fa', 参: 'can', 响: 'xiang', 应: 'ying', 返: 'fan',
  回: 'hui', 错: 'cuo', 误: 'wu', 成: 'cheng', 失: 'shi', 败: 'bai',
  始: 'shi', 完: 'wan', 暂: 'zan', 继: 'ji', 续: 'xu',
  止: 'zhi', 运: 'yun', 全: 'quan', 局: 'ju', 部: 'bu',
  当: 'dang', 最: 'zui', 第: 'di', 个: 'ge', 每: 'mei', 次: 'ci',
  如: 'ru', 果: 'guo', 否: 'fou', 是: 'shi', 不: 'bu', 或: 'huo',
  且: 'qie', 非: 'fei', 与: 'yu', 及: 'ji', 到: 'dao', 从: 'cong',
  至: 'zhi', 为: 'wei', 被: 'bei', 把: 'ba', 给: 'gei', 让: 'rang',
  使: 'shi', 得: 'de', 可: 'ke', 以: 'yi', 会: 'hui',
  要: 'yao', 需: 'xu', 必: 'bi', 须: 'xu', 该: 'gai',
  按: 'an', 照: 'zhao', 根: 'gen', 依: 'yi', 通: 'tong', 知: 'zhi', 经: 'jing',
  由: 'you', 向: 'xiang', 于: 'yu', 在: 'zai', 中: 'zhong',
  外: 'wai', 左: 'zuo', 右: 'you', 里: 'li', 边: 'bian', 旁: 'pang',
  底: 'di', 顶: 'ding', 端: 'duan', 头: 'tou', 尾: 'wei',
  首: 'shou', 末: 'mo', 初: 'chu', 终: 'zhong', 原: 'yuan', 现: 'xian',
  旧: 'jiu', 老: 'lao', 少: 'shao', 多: 'duo', 几: 'ji',
  些: 'xie', 某: 'mou', 各: 'ge', 另: 'ling', 其: 'qi', 他: 'ta',
  她: 'ta', 它: 'ta', 们: 'men', 自: 'zi', 己: 'ji', 我: 'wo',
  你: 'ni', 您: 'nin', 这: 'zhe', 那: 'na', 哪: 'na', 什: 'shen',
  么: 'me', 怎: 'zen', 样: 'yang', 何: 'he',
  啥: 'sha', 谁: 'shui', 儿: 'er', 呢: 'ne',
  吗: 'ma', 吧: 'ba', 啊: 'a', 呀: 'ya', 哦: 'o', 嗯: 'en',
  好: 'hao', 坏: 'huai', 假: 'jia',
  快: 'kuai', 慢: 'man', 早: 'zao', 晚: 'wan', 先: 'xian', 再: 'zai',
  还: 'hai', 又: 'you', 也: 'ye', 都: 'dou', 只: 'zhi', 就: 'jiu',
  才: 'cai', 已: 'yi', 曾: 'ceng', 将: 'jiang',
  想: 'xiang', 愿: 'yuan', 肯: 'ken', 敢: 'gan', 叫: 'jiao',
  帮: 'bang', 助: 'zhu', 支: 'zhi', 持: 'chi',
  聚: 'ju', 焦: 'jiao', 激: 'ji', 活: 'huo',
  供: 'gong', 予: 'yu', 赠: 'zeng', 交: 'jiao',
  付: 'fu', 收: 'shou', 受: 'shou', 拿: 'na',
  摆: 'bai', 挂: 'gua', 粘: 'zhan', 装: 'zhuang',
  卸: 'xie', 拆: 'chai', 修: 'xiu', 改: 'gai',
  整: 'zheng', 排: 'pai', 序: 'xu', 顺: 'shun', 倒: 'dao',
  翻: 'fan', 旋: 'xuan', 绕: 'rao', 围: 'wei', 圈: 'quan',
  圆: 'yuan', 形: 'xing', 角: 'jiao', 线: 'xian', 面: 'mian',
  体: 'ti', 积: 'ji', 轻: 'qing',
  厚: 'hou', 薄: 'bao', 深: 'shen', 浅: 'qian', 宽: 'kuan', 窄: 'zhai',
  粗: 'cu', 细: 'xi', 密: 'mi', 稀: 'xi', 紧: 'jin', 松: 'song',
  硬: 'ying', 软: 'ruan', 干: 'gan', 湿: 'shi', 冷: 'leng', 热: 're',
  温: 'wen', 凉: 'liang', 暖: 'nuan', 烫: 'tang', 冰: 'bing', 火: 'huo',
  水: 'shui', 土: 'tu', 木: 'mu', 金: 'jin', 石: 'shi', 沙: 'sha',
  泥: 'ni', 灰: 'hui', 尘: 'chen', 烟: 'yan', 雾: 'wu', 云: 'yun',
  雨: 'yu', 雪: 'xue', 风: 'feng', 雷: 'lei', 电: 'dian', 光: 'guang',
  影: 'ying', 色: 'se', 红: 'hong', 橙: 'cheng', 黄: 'huang', 绿: 'lv',
  青: 'qing', 蓝: 'lan', 紫: 'zi', 黑: 'hei', 白: 'bai',
  粉: 'fen', 棕: 'zong', 褐: 'he', 银: 'yin', 铜: 'tong',
  铁: 'tie', 钢: 'gang', 铝: 'lv', 锌: 'xin', 铅: 'qian', 锡: 'xi',
  // 媒体处理相关
  频: 'pin', 压: 'ya', 缩: 'suo', 裁: 'cai', 媒: 'mei',
  脸: 'lian', 夹: 'jia', 语: 'yu', 报: 'bao',
  // 格式工厂相关
  厂: 'chang', 批: 'pi', 帧: 'zhen', 率: 'lv',
  // 实用工具相关
  哈: 'ha', 希: 'xi', 戳: 'chuo', 校: 'xiao', 摘: 'zhai', 十: 'shi', 六: 'liu',
  混: 'hun', 背: 'bei', 景: 'jing', 轨: 'gui', 道: 'dao',
  倍: 'bei', 速: 'su', 辨: 'bian', 节: 'jie', 摄: 'she',
  // 新增实用工具模块相关
  生: 'sheng',
  // 文档转换和图像处理相关
  档: 'dang', 糊: 'hu', 锐: 'rui', 彩: 'cai', 衡: 'heng',
  略: 'lve', 滤: 'lv', 简: 'jian',
  // 文件操作相关
  创: 'chuang',
  // 查看图片相关
  看: 'kan', 预: 'yu', 览: 'lan',
  // 元素操作相关
  兄: 'xiong', 弟: 'di', 姐: 'jie', 妹: 'mei',
  // AI智能爬虫相关
  爬: 'pa', 虫: 'chong',
  // 其他常用字
  户: 'hu', 笺: 'jian', 签: 'qian',
  // 模块名称补充
  宏: 'hong', 便: 'bian', 笔: 'bi', 记: 'ji',
  监: 'jian', 听: 'ting', 捕: 'bu', 套: 'tao', 化: 'hua',
  函: 'han', 睡: 'shui', 眠: 'mian',
  阻: 'zu', 塞: 'sai', 抽: 'chou', 奖: 'jiang', 概: 'gai',
  权: 'quan', 延: 'yan', 迟: 'chi',
  触: 'chu', 常: 'chang', 捷: 'jie',
  桌: 'zhuo', 壁: 'bi', 亮: 'liang',
  暗: 'an', 静: 'jing', 默: 'mo', 弃: 'qi', 跃: 'yue',
  窜: 'cuan', 逃: 'tao', 逸: 'yi', 遁: 'dun', 隐: 'yin',
  藏: 'cang', 显: 'xian', 露: 'lu', 浮: 'fu', 沉: 'chen',
  升: 'sheng', 降: 'jiang', 增: 'zeng', 减: 'jian', 乘: 'cheng',
  余: 'yu', 商: 'shang',
  和: 'he',
  // 模块名称补充2 - 确保所有模块名称字符都有映射
  采: 'cai', 集: 'ji', 拟: 'ni', 轮: 'lun', 休: 'xiu',
  // 关键词补充 - 确保搜索关键词中的汉字都有映射
  浏: 'liu', 钮: 'niu', 留: 'liu', 填: 'tian', 史: 'shi',
  确: 'que', 认: 'ren', 赋: 'fu', 期: 'qi',
  滴: 'di', 歌: 'ge', 曲: 'qu', 物: 'wu', 离: 'li',
  切: 'qie', 段: 'duan', 直: 'zhi', 镜: 'jing', 封: 'feng',
  烧: 'shao', 尺: 'chi', 寸: 'cun', 检: 'jian', 测: 'ce',
  身: 'shen', 份: 'fen', 扫: 'sao', 描: 'miao', 拷: 'kao',
  贝: 'bei', 副: 'fu', 建: 'jian', 产: 'chan', 匹: 'pi',
  找: 'zhao', 串: 'chuan', 引: 'yin', 象: 'xiang',
  口: 'kou', 谱: 'pu', 嵌: 'qian', 域: 'yu', 说: 'shuo',
  登: 'deng', 陆: 'lu', 句: 'ju', 辑: 'ji',
  // QQ自动化相关
  私: 'si', 聊: 'liao', 群: 'qun', 友: 'you', 员: 'yuan', 账: 'zhang', 号: 'hao',
  // 代理抓包相关
  代: 'dai',
  // 补充缺失的汉字 - 确保所有模块名称和关键词都能搜索
  避: 'bi', 布: 'bu', 步: 'bu', 层: 'ceng', 场: 'chang', 超: 'chao', 撤: 'che',
  的: 'de', 二: 'er', 辅: 'fu', 共: 'gong', 耗: 'hao', 很: 'hen', 画: 'hua',
  际: 'ji', 界: 'jie', 禁: 'jin', 具: 'ju', 跨: 'kua', 栏: 'lan', 了: 'le',
  力: 'li', 逻: 'luo', 没: 'mei', 免: 'mian', 纳: 'na', 偏: 'pian', 射: 'she',
  殊: 'shu', 算: 'suan', 特: 'te', 同: 'tong', 微: 'wei',
  // 补充更多缺失的汉字
  维: 'wei', 未: 'wei', 无: 'wu', 限: 'xian', 相: 'xiang', 详: 'xiang', 享: 'xiang',
  消: 'xiao', 销: 'xiao', 意: 'yi', 映: 'ying', 杂: 'za', 之: 'zhi',
  质: 'zhi', 钟: 'zhong', 追: 'zhui', 做: 'zuo',
  // 屏幕共享相关
  投: 'tou',
  // 触发器关键词补充
  周: 'zhou', 箱: 'xiang', 钩: 'gou', 隔: 'ge',
}

/**
 * 获取单个汉字的拼音
 */
function getCharPinyin(char: string): string {
  return pinyinMap[char] || char.toLowerCase()
}

/**
 * 获取单个汉字的拼音首字母
 */
function getCharInitial(char: string): string {
  const pinyin = pinyinMap[char]
  return pinyin ? pinyin[0] : char.toLowerCase()
}

/**
 * 获取字符串的完整拼音
 */
export function getPinyin(str: string): string {
  return str.split('').map(getCharPinyin).join('')
}

/**
 * 获取字符串的拼音首字母
 */
export function getPinyinInitials(str: string): string {
  return str.split('').map(getCharInitial).join('')
}

/**
 * 拼音模糊匹配
 * @param text 要搜索的文本
 * @param query 搜索关键词
 * @returns 是否匹配
 */
export function pinyinMatch(text: string, query: string): boolean {
  if (!query) return true
  if (!text) return false
  
  const lowerText = text.toLowerCase()
  const lowerQuery = query.toLowerCase()
  
  // 1. 直接包含匹配
  if (lowerText.includes(lowerQuery)) return true
  
  // 2. 拼音全拼匹配
  const textPinyin = getPinyin(text)
  if (textPinyin.includes(lowerQuery)) return true
  
  // 3. 拼音首字母匹配
  const textInitials = getPinyinInitials(text)
  if (textInitials.includes(lowerQuery)) return true
  
  // 4. 混合匹配（支持部分拼音部分汉字）
  let textIndex = 0
  let queryIndex = 0
  
  while (textIndex < text.length && queryIndex < query.length) {
    const textChar = text[textIndex]
    const queryChar = query[queryIndex]
    
    // 如果查询字符是汉字，直接比较
    if (/[\u4e00-\u9fa5]/.test(queryChar)) {
      if (textChar === queryChar) {
        textIndex++
        queryIndex++
      } else {
        textIndex++
      }
    } else {
      // 查询字符是拼音，尝试匹配
      const charPinyin = getCharPinyin(textChar)
      const charInitial = getCharInitial(textChar)
      
      // 尝试匹配完整拼音
      let matched = false
      for (let len = charPinyin.length; len >= 1; len--) {
        const pinyinPart = charPinyin.substring(0, len)
        const queryPart = query.substring(queryIndex, queryIndex + len).toLowerCase()
        if (pinyinPart === queryPart) {
          queryIndex += len
          matched = true
          break
        }
      }
      
      // 尝试匹配首字母
      if (!matched && charInitial === queryChar.toLowerCase()) {
        queryIndex++
        matched = true
      }
      
      textIndex++
    }
  }
  
  return queryIndex >= query.length
}
