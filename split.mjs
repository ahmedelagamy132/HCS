import * as fs from 'fs';
import * as path from 'path';
import * as cheerio from 'cheerio';

const pages = [
  { file: 'dashboard.html',   id: 'tab-overview' },
  { file: 'clients.html',     id: 'tab-clients' },
  { file: 'stables.html',     id: 'tab-stables' },
  { file: 'horses.html',      id: 'tab-horses' },
  { file: 'admins.html',      id: 'tab-admins' },
  { file: 'ai-models.html',   id: 'tab-ai-models' },
  { file: 'reports.html',     id: 'tab-reports' },
  { file: 'settings.html',    id: 'tab-settings' },
];

const DIR = "admin";

for (const { file, id } of pages) {
  const filePath = path.join(DIR, file);
  if (!fs.existsSync(filePath)) continue;

  const html = fs.readFileSync(filePath, 'utf-8');
  const $ = cheerio.load(html);

  // Replace content of body with our new layout pieces, retaining ONLY the active tab content
  const activeTabHTML = $(`#${id}`).html();

  $('aside.sidebar').replaceWith('<div id="sidebar-container"></div>');
  $('.topbar').replaceWith('<div id="header-container"></div>');

  // Clear everything in .content to start fresh
  $('.content').empty();
  
  // Create a new tab div matching the active one, without display:none
  $('.content').append(`
    <div class="tab-view active" id="${id}" style="display:block">
      ${activeTabHTML}
    </div>
  `);

  // Remove the old layout script and generic index scripts from the end of body
  $('body > script').remove(); 
  
  // Add layout.js at end of body
  $('body').append('\n<script src="/admin/js/layout.js"></script>\n');
  $('body').append(`\n<script src="/admin/js/${file.replace(".html", ".js")}"></script>\n`);

  fs.writeFileSync(filePath, $.html());
  console.log(`Processed ${filePath} - Kept #${id}`);
  
  // While here, make an empty js file for it
  const jsPath = path.join(DIR, "js", file.replace(".html", ".js"));
  if (!fs.existsSync(jsPath)) {
    fs.writeFileSync(jsPath, `// Code for ${file}\nfunction initPage() {\n  // API calls for ${file}\n}\n`);
  }
}
