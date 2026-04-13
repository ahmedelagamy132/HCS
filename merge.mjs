import fs from 'fs';
import * as cheerio from 'cheerio';

const HTML_AI = 'admin/ai-models.html';
const HTML_TEST = 'admin/model-testing.html';
const JS_AI = 'admin/js/ai-models.js';
const JS_TEST = 'admin/js/model-testing.js';

let $ai = cheerio.load(fs.readFileSync(HTML_AI, 'utf-8'));
let $test = cheerio.load(fs.readFileSync(HTML_TEST, 'utf-8'));

// 1. Get CSS from model-testing.html (extracting only the unique parts)
const testStyleStr = $test('style').html();
// We'll extract CSS appended at the end after padding things like `/* --- WORKSPACE --- */` or `/* --- MODEL SELECTOR --- */`
const extraCssStart = testStyleStr.indexOf('/* ─── MODEL SELECTOR');
let extraCss = extraCssStart > -1 ? testStyleStr.substring(extraCssStart) : testStyleStr.substring(testStyleStr.indexOf('/* --- MODEL SELECTOR'));
if (!extraCss || extraCss.length < 10) {
    extraCss = testStyleStr.substring(testStyleStr.indexOf('/* ─── BADGE'));
}
// Strip out .vision-notice from the extraccs
extraCss = extraCss.replace(/\.vision-notice\s*\{[^}]+\}/g, '');
extraCss = extraCss.replace(/\.vn-dot\s*\{[^}]+\}/g, '');
extraCss = extraCss.replace(/\.vn-text\s*[^}]*\}/g, '');

// Append to ai-models CSS
let aiStyle = $ai('style').html();
$ai('style').html(aiStyle + '\n' + extraCss);

// 2. Build Tabs in ai-models
const originalGrid = $ai('#model-grid').parent().html();
$ai('#model-grid').parent().html(`
    <div class="page-tabs">
      <div class="pt-item active" onclick="switchAITab('deployed')">All Models</div>
      <div class="pt-item" onclick="switchAITab('vision')">Vision Testing</div>
    </div>
    
    <div id="tab-deployed" class="pt-content active">
      ${originalGrid}
    </div>
    
    <div id="tab-vision" class="pt-content">
      ${$test('#model-selector').length ? $test('#model-selector').prop('outerHTML') : $test('.model-selector').prop('outerHTML')}
      ${$test('#workspace').length ? $test('#workspace').prop('outerHTML') : $test('.workspace').prop('outerHTML')}
    </div>
`);

// Add the switchAITab script logic
$ai('body').append(`
<script>
function switchAITab(tab) {
  document.querySelectorAll('.pt-item').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.pt-content').forEach(el => el.classList.remove('active'));
  
  event.target.classList.add('active');
  document.getElementById('tab-' + tab).classList.add('active');
}
</script>
`);

// Include the model-testing.js script
$ai('body').append('<script src="/admin/js/model-testing-merged.js"></script>');

fs.writeFileSync(HTML_AI, $ai.html());

// 3. Fix JS conflicts (both use initPage)
// Create a new model-testing-merged.js where initPage -> initVisionPage
let testJs = fs.readFileSync(JS_TEST, 'utf-8');
testJs = testJs.replace('function initPage()', 'function initVisionTestingPage()');
fs.writeFileSync('admin/js/model-testing-merged.js', testJs);

// In ai-models.js we also invoke the testing initializer
let aiJs = fs.readFileSync(JS_AI, 'utf-8');
if (!aiJs.includes('initVisionTestingPage()')) {
  aiJs = aiJs.replace('} catch (error) {', '} \n    if (typeof initVisionTestingPage === "function") initVisionTestingPage();\n  } catch (error) {');
}
fs.writeFileSync(JS_AI, aiJs);

console.log('Successfully merged!');
