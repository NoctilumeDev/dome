import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import vm from 'node:vm';
import { createRequire } from 'node:module';

const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.dirname(here),
  output = path.join(here, '_site'),
  temporary = path.join(here, '.build/library');
function copy(source, target) {
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.cpSync(source, target, { recursive: true, force: true });
}
function run(command, args, cwd) {
  const result = spawnSync(command, args, {
    cwd,
    stdio: 'inherit',
    env: {
      ...process.env,
      VUE_APP_API_BASE_URL: '/demo-api',
      PATH: path.dirname(process.execPath) + path.delimiter + process.env.PATH,
    },
  });
  if (result.status !== 0) throw new Error(`Build failed: ${command}`);
}
fs.mkdirSync(output, { recursive: true });
copy(path.join(here, 'index.html'), path.join(output, 'index.html'));
copy(path.join(here, 'shared'), path.join(output, 'shared'));
fs.writeFileSync(path.join(output, '.nojekyll'), '');

// Build the original library frontend in a disposable directory. Production sources stay intact.
const library = path.join(repo, 'coursework/library-management-system/frontend');
if (!process.argv.includes('--skip-library')) {
  fs.mkdirSync(temporary, { recursive: true });
  for (const entry of fs.readdirSync(library))
    if (!['node_modules', 'dist', '.git'].includes(entry))
      copy(path.join(library, entry), path.join(temporary, entry));
  const dependencies = path.join(temporary, 'node_modules');
  if (!fs.existsSync(dependencies))
    fs.symlinkSync(
      path.join(library, 'node_modules'),
      dependencies,
      process.platform === 'win32' ? 'junction' : 'dir'
    );
  const requestPath = path.join(temporary, 'src/utils/request.js');
  const adapterImport = path
    .relative(path.dirname(requestPath), path.join(here, 'library/adapter.mjs'))
    .replaceAll('\\', '/');
  fs.writeFileSync(
    requestPath,
    `import axios from 'axios';\nimport { createLibraryAdapter } from '${adapterImport}';\nexport default axios.create({ baseURL: '/demo-api', adapter: createLibraryAdapter() });\n`
  );
  const storagePath = path.join(temporary, 'src/utils/storage.js');
  fs.writeFileSync(
    storagePath,
    fs
      .readFileSync(storagePath, 'utf8')
      .replace(
        'sessionStorage.clear();',
        "['token', 'health-info', 'active_key'].forEach(key => sessionStorage.removeItem(key));"
      )
  );
  const assistantPath = path.join(temporary, 'src/views/assistant/BookAssistant.vue');
  const assistantCopy = fs
    .readFileSync(assistantPath, 'utf8')
    .replaceAll('数据库已核验', '演示数据已匹配')
    .replaceAll('本地范围已处理', '演示范围已处理')
    .replace(
      'DeepSeek 是可选的语义理解层，只负责提高自然语言召回；最终答案始终以馆藏数据库为准。',
      '浏览器演示仅匹配内置馆藏样例，没有调用大模型或数据库。下方是原项目的安全处理流程示意，完整能力请查看源码。'
    )
    .replace('问答安全处理流程', '原项目安全处理流程示意')
    .replace('可降级，但不越过安全边界', '先体验页面，再运行完整项目')
    .replace(
      'DeepSeek 可用时负责理解口语和提高查全率；未配置或暂时不可用时，系统改用本地规则，复杂表达可能漏检，但范围过滤、参数化查询和数据库事实回答保持不变。',
      '这里提供简单样例匹配，复杂表达可能无法命中。模型理解、参数化查询和数据库权限校验需要运行原项目后端才能体验。'
    )
    .replace('安全性保持', '本地样例')
    .replace('自然语言召回降低', '不连接模型')
    .replace(
      '天气、股票、闲聊等问题会在本地直接拒绝，不消耗模型 API。',
      '输入仅在当前浏览器处理，可试试具体书名、作者、分类或本人的借阅。'
    )
    .replace(
      '可以查具体书名，也可以按作者、分类、出版社或可借状态筛选。',
      '可以试试书名《三体》、作者余华、计算机分类或本人借阅。'
    );
  fs.writeFileSync(assistantPath, assistantCopy);
  for (const role of ['user', 'admin']) {
    const home = path.join(temporary, `src/views/${role}/Home.vue`);
    fs.writeFileSync(
      home,
      fs
        .readFileSync(home, 'utf8')
        .replaceAll('在线服务已连接到后端', '浏览器本地演示已就绪')
        .replaceAll('用自然语言查询数据库里的图书信息。', '用简单问题查询虚构的演示馆藏。')
    );
  }
  for (const name of ['BookManage', 'UserManage']) {
    const file = path.join(temporary, `src/views/admin/${name}.vue`);
    fs.writeFileSync(
      file,
      fs
        .readFileSync(file, 'utf8')
        .replace('<el-upload', '<el-upload :disabled="true"')
        .replace('点击上传', '演示版不上传文件')
    );
  }
  const libraryIndex = path.join(temporary, 'public/index.html');
  fs.writeFileSync(
    libraryIndex,
    fs
      .readFileSync(libraryIndex, 'utf8')
      .replace(
        '</head>',
        '<link rel="stylesheet" href="../shared/shell.css"><script src="../shared/shell.js"></script></head>'
      )
  );
  fs.appendFileSync(
    path.join(temporary, 'vue.config.js'),
    '\nmodule.exports.productionSourceMap = false;\n'
  );
  run(
    process.execPath,
    [
      path.join(library, 'node_modules/@vue/cli-service/bin/vue-cli-service.js'),
      'build',
      '--dest',
      path.join(output, 'library'),
    ],
    temporary
  );
  console.log('Library frontend built from original Vue components.');
}

const dorm = path.join(
  repo,
  'independent-projects/dormitory-management-system/src/main/resources/static'
);
copy(dorm, path.join(output, 'dormitory'));
copy(path.join(here, 'dormitory/adapter.mjs'), path.join(output, 'dormitory/adapter.mjs'));
for (const filename of ['index.html', 'login.html']) {
  const file = path.join(output, 'dormitory', filename);
  let html = fs
    .readFileSync(file, 'utf8')
    .replace(
      '</head>',
      '<link rel="stylesheet" href="../shared/shell.css"><script src="../shared/shell.js"></script></head>'
    );
  html = html.replace('<script src="app.js', '<script type="module" src="app.js');
  html = html.replace('<script>', '<script type="module">\nimport "./adapter.mjs";');
  html = html.replace(
    '`${window.location.origin}/index.html`',
    "new URL('index.html', window.location.href).href"
  );
  fs.writeFileSync(file, html);
}
const dormApp = path.join(output, 'dormitory/app.js');
const dormSource = fs.readFileSync(dormApp, 'utf8');
const inlineHandlers = [
  ...new Set([...dormSource.matchAll(/onclick="([A-Za-z_][\w]*)\(/g)].map((match) => match[1])),
];
fs.writeFileSync(
  dormApp,
  'import "./adapter.mjs";\n' +
    dormSource +
    '\nObject.assign(window, {' +
    inlineHandlers.join(',') +
    '});\n'
);
console.log('Dormitory pages copied with a browser-only data adapter.');

const mini = path.join(repo, 'qingye/miniprogram');
for (const filename of ['index.html', 'browser.css', 'runtime.mjs', 'model.mjs']) {
  copy(path.join(here, 'qingye', filename), path.join(output, 'qingye', filename));
}
copy(path.join(mini, 'assets'), path.join(output, 'qingye/assets'));
copy(
  path.join(library, 'node_modules/vue/dist/vue.min.js'),
  path.join(output, 'qingye/vue.min.js')
);
copy(path.join(library, 'node_modules/vue/LICENSE'), path.join(output, 'qingye/vue-LICENSE.txt'));
const python =
  process.env.DEMO_PYTHON ||
  (process.platform === 'win32' ? 'D:\\python-3.10.6\\python.exe' : 'python3');
run(
  python,
  [
    '-X',
    'utf8',
    path.join(here, 'qingye/convert_wxml.py'),
    mini,
    path.join(output, 'qingye/templates.js'),
  ],
  repo
);
const templateContext = { window: {} };
vm.runInNewContext(
  fs.readFileSync(path.join(output, 'qingye/templates.js'), 'utf8'),
  templateContext
);
const compiler = createRequire(path.join(library, 'package.json'))('vue-template-compiler');
for (const [name, item] of Object.entries(templateContext.window.QingyeTemplates)) {
  if (!item.template) continue;
  const result = compiler.compile(item.template);
  if (result.errors.length)
    throw new Error('Qingye template error (' + name + '): ' + result.errors.join('; '));
}
let sources = 'window.QingyeSources = {\n';
for (const folder of fs.readdirSync(path.join(mini, 'pages'))) {
  const file = path.join(mini, 'pages', folder, 'index.js');
  if (fs.existsSync(file))
    sources += `${JSON.stringify(
      `pages/${folder}/index`
    )}:function(module,exports,require){\n${fs.readFileSync(file, 'utf8')}\n},\n`;
}
for (const name of ['view', 'navigation', 'request-error'])
  sources += `${JSON.stringify(
    `utils/${name}`
  )}:function(module,exports,require){\n${fs.readFileSync(
    path.join(mini, 'utils', name + '.js'),
    'utf8'
  )}\n},\n`;
sources += '};\n';
fs.writeFileSync(path.join(output, 'qingye/sources.js'), sources);
console.log('Qingye WXML, styles, assets and page logic compiled for browser preview.');
const game = path.join(repo, 'independent-projects/dianjing/static');
if (fs.existsSync(game)) {
  copy(game, path.join(output, 'dianjing'));
  console.log('Dianjing game copied.');
}
console.log('Site ready: ' + output);
