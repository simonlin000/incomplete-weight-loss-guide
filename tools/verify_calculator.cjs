const fs = require('node:fs');
const assert = require('node:assert/strict');
const {createRequire} = require('node:module');
const path = require('node:path');
const repo = path.resolve(__dirname, '..');
const req = createRequire(path.join(repo, 'package.json'));
const {ref, computed} = req('vue');
const file = path.join(repo, 'docs/.vitepress/theme/components/CalorieCalc.vue');
const source = fs.readFileSync(file, 'utf8');
const script = source.match(/<script setup>([\s\S]*?)<\/script>/)[1].replace(/^import .*?from 'vue'\s*$/m, '');
const expose = ['sex','age','height','weight','target','activity','pregnant','needsProfessional','bmi','bmr','tdee','intake','deficit','protein','canGuide','eligibilityReason','restored','reset'];
const run = new Function('ref','computed','onMounted','watch','localStorage',script + '\nreturn {'+expose.join(',')+'}');
let count = 0;
function instance(saved) {
  const entries = new Map(saved ? [['simonlin-calc-v1', JSON.stringify(saved)]] : []);
  const mounts = [], watchers = [];
  const storage = {getItem:k=>entries.get(k)||null,setItem:(k,v)=>entries.set(k,v),removeItem:k=>entries.delete(k)};
  const data = run(ref, computed, f=>mounts.push(f), (_,f)=>watchers.push(f), storage);
  return {data, entries, mount:()=>mounts.forEach(f=>f()), save:()=>watchers.forEach(f=>f())};
}
function fixture(values) {
  const x=instance(); for(const [k,v] of Object.entries(values))x.data[k].value=v; return x;
}
function check(name, body) {body();count++;process.stdout.write('通过：'+name+'\n');}
check('普通超重成人采用正文例一公式',()=>{
 const d=fixture({sex:'male',age:40,height:175,weight:90,activity:1.375}).data;
 assert.equal(d.canGuide.value,true);assert.equal(d.bmr.value,1798.75);
 assert.equal(d.tdee.value,2473.28125);assert.equal(d.intake.value,1973.28125);
});
check('低活动量女性接受较小缺口',()=>{
 const d=fixture({sex:'female',age:32,height:162,weight:70,activity:1.2}).data;
 assert.equal(d.bmr.value,1391.5);assert.equal(d.intake.value,1391.5);
 assert.ok(Math.abs(d.deficit.value-278.3)<1e-8);
});
for(const [name,values] of [
 ['偏瘦',{sex:'female',age:25,height:165,weight:45}],
 ['正常体重',{sex:'female',age:30,height:165,weight:60}],
 ['BMI边界正常',{height:200,weight:95.99}],
 ['65岁',{age:65,weight:100}],['80岁',{age:80,weight:100}],
 ['未成年',{age:17}],['孕哺',{pregnant:true}],
 ['需专业评估',{needsProfessional:true}],['无效身高',{height:0}],
 ['无效体重',{weight:NaN}],['无效年龄',{age:null}],
])check(name+'不输出减重目标',()=>{
 const d=fixture(values).data;assert.equal(d.canGuide.value,false);
 assert.equal(d.intake.value,null);assert.equal(d.deficit.value,null);assert.equal(d.protein.value,null);
});
check('BMI24边界可进入演算',()=>assert.equal(fixture({height:200,weight:96}).data.canGuide.value,true));
check('18岁超重成人可进入演算',()=>assert.equal(fixture({age:18,weight:100}).data.canGuide.value,true));
for(const target of [-1,40,200,Infinity])check('无效目标体重不产生蛋白目标 '+target,()=>{
 assert.equal(fixture({target}).data.protein.value,null);
});
check('恢复本机记录并准确提示',()=>{
 const x=instance({sex:'female',age:35,height:165,weight:80,activity:1.55,pregnant:true});
 x.mount();assert.equal(x.data.weight.value,80);assert.equal(x.data.restored.value,true);
 assert.equal(x.data.canGuide.value,false);
});
check('保存内容与页面披露一致',()=>{
 const x=instance();x.data.needsProfessional.value=true;x.save();
 const saved=JSON.parse(x.entries.get('simonlin-calc-v1'));
 assert.deepEqual(Object.keys(saved).sort(),['sex','age','height','weight','target','activity','bodyFat','waist','pregnant'].sort());
});
check('清空真正删除保存记录',()=>{
 const x=instance({weight:100});x.mount();x.data.reset();x.save();
 assert.equal(x.entries.has('simonlin-calc-v1'),false);
 assert.equal(x.data.needsProfessional.value,false);assert.equal(x.data.restored.value,false);
});
check('结果区受适用性判断控制，取消线性周数预报',()=>{
 assert.match(source,/v-if="!canGuide"/);assert.doesNotMatch(source,/weeksTo5|weekly\.toFixed|110 千卡/);
});
console.log('合计 '+count+' 项通过；直接执行组件中的计算与存储逻辑。');
