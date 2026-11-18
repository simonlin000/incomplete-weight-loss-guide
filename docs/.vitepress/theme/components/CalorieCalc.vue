<script setup>
import { ref, computed, onMounted, watch } from 'vue'

const sex = ref('male')
const age = ref(30)
const height = ref(175)
const weight = ref(85)
const target = ref(null)
const activity = ref(1.375)
const bodyFat = ref(null)
const waist = ref(null)
const pregnant = ref(false)
const needsProfessional = ref(false)

const actOpts = [
  { v: 1.2, label: '基本不动（坐办公室，几乎不运动）' },
  { v: 1.375, label: '全天总体轻度活动，有些走动与轻运动' },
  { v: 1.55, label: '全天总体中等活动，日常走动较多并有训练' },
  { v: 1.725, label: '全天总体高活动，较多体力工作或高运动量' },
  { v: 1.9, label: '运动员、一天两练' },
]

const num = (v) => (v === null || v === '' || isNaN(Number(v)) ? null : Number(v))

// 把上次填的数留在这台设备的浏览器里，下次打开自动填上
const KEY = 'simonlin-calc-v1'
const restored = ref(false)

onMounted(() => {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return
    const d = JSON.parse(raw)
    if (!d || typeof d !== 'object') return
    if (d.sex === 'male' || d.sex === 'female') sex.value = d.sex
    const put = (r, v) => {
      if (v === null || v === undefined || v === '') return
      const n = Number(v)
      if (Number.isFinite(n)) r.value = n
    }
    put(age, d.age)
    put(height, d.height)
    put(weight, d.weight)
    put(target, d.target)
    put(bodyFat, d.bodyFat)
    put(waist, d.waist)
    if (actOpts.some((o) => o.v === Number(d.activity))) activity.value = Number(d.activity)
    pregnant.value = d.pregnant === true
    restored.value = true
  } catch (e) {
    /* 存的东西坏了就当没存过 */
  }
})

let skipNext = false

watch([sex, age, height, weight, target, activity, bodyFat, waist, pregnant], () => {
  if (skipNext) {
    skipNext = false
    return
  }
  try {
    localStorage.setItem(
      KEY,
      JSON.stringify({
        sex: sex.value,
        age: age.value,
        height: height.value,
        weight: weight.value,
        target: target.value,
        activity: activity.value,
        bodyFat: bodyFat.value,
        waist: waist.value,
        pregnant: pregnant.value,
      })
    )
  } catch (e) {
    /* 隐私模式写不了，算了 */
  }
})

function reset() {
  sex.value = 'male'
  age.value = 30
  height.value = 175
  weight.value = 85
  target.value = null
  activity.value = 1.375
  bodyFat.value = null
  waist.value = null
  pregnant.value = false
  needsProfessional.value = false
  restored.value = false
  skipNext = true
  try {
    localStorage.removeItem(KEY)
  } catch (e) {}
}

const h = computed(() => num(height.value))
const w = computed(() => num(weight.value))
const a = computed(() => num(age.value))

const valid = computed(
  () => h.value > 100 && h.value < 230 && w.value > 25 && w.value < 300 && a.value >= 18 && a.value <= 100
)

// 2.8：BMI
const bmi = computed(() => (valid.value ? w.value / (h.value / 100) / (h.value / 100) : null))
const bmiBand = computed(() => {
  if (bmi.value == null) return null
  if (bmi.value < 18.5) return { text: '偏瘦', tone: 'warn' }
  if (bmi.value < 24) return { text: '正常', tone: 'ok' }
  if (bmi.value < 28) return { text: '超重', tone: 'warn' }
  return { text: '肥胖', tone: 'alert' }
})
const eligibilityReason = computed(() => {
  if (!valid.value) return '请填写有效的年龄、身高和体重。未成年人不使用这个成人计算器。'
  if (pregnant.value) return '孕期或哺乳期不使用本工具安排减重，先由产科或营养专业人员评估。'
  if (a.value >= 65) return '65 岁及以上的体重目标、肌肉和营养需求需要个体评估，本工具不输出自行减重目标。'
  if (needsProfessional.value) return '有基础病、用药、术后恢复或进食障碍等情况，先由专业人员确定是否及怎样减重。'
  if (bmi.value < 18.5) return '目前 BMI 属于偏瘦范围，不输出减重热量缺口。请先评估营养和健康状况。'
  if (bmi.value < 24) return '目前 BMI 在正常范围，本工具不自动建议热量缺口。可关注体能、抗阻和腰围；如腰围偏大，先作个体评估。'
  return ''
})
const canGuide = computed(() => eligibilityReason.value === '')
const normalLow = computed(() => (valid.value ? 18.5 * (h.value / 100) ** 2 : null))
const normalHigh = computed(() => (valid.value ? 23.9 * (h.value / 100) ** 2 : null))

// 2.3 第一步：Mifflin-St Jeor（R8）
const bmr = computed(() => {
  if (!valid.value) return null
  const base = 10 * w.value + 6.25 * h.value - 5 * a.value
  return sex.value === 'male' ? base + 5 : base - 161
})

// 若填了体脂率，给出去脂体重口径（R8 的 19.7×FFM+413）
const ffm = computed(() => {
  const bf = num(bodyFat.value)
  if (!valid.value || bf == null || bf <= 3 || bf >= 60) return null
  const lean = w.value * (1 - bf / 100)
  return { lean, bmr: 19.7 * lean + 413 }
})

// 2.3 第二步：TDEE
const tdee = computed(() => (bmr.value == null ? null : bmr.value * Number(activity.value)))

// 2.3 第三步：缺口与底线（不低于基础代谢）
const intakeRaw = computed(() => (canGuide.value ? tdee.value - 500 : null))
const floored = computed(() => intakeRaw.value != null && intakeRaw.value < bmr.value)
const intake = computed(() => {
  if (intakeRaw.value == null) return null
  return Math.max(intakeRaw.value, bmr.value)
})
const deficit = computed(() => (intake.value == null ? null : tdee.value - intake.value))
const portions = computed(() => (intake.value == null ? null : intake.value / 90))

// 3.2：蛋白质按目标体重，1.2～1.6 克/公斤
const targetWeight = computed(() => {
  const t = num(target.value)
  if (t != null) return Number.isFinite(t) && t >= normalLow.value && t <= w.value ? t : null
  return normalHigh.value ? Math.round(normalHigh.value * 10) / 10 : null
})
const protein = computed(() => {
  if (!canGuide.value || !targetWeight.value) return null
  return { low: Math.round(targetWeight.value * 1.2), high: Math.round(targetWeight.value * 1.6) }
})

// 2.8：腰围
const waistBand = computed(() => {
  const wa = num(waist.value)
  if (!wa) return null
  const cut = sex.value === 'male' ? 90 : 85
  const upper = sex.value === 'male' ? 85 : 80
  if (wa >= cut) return { text: '中心型肥胖', tone: 'alert' }
  if (wa >= upper) return { text: '中心型肥胖前期', tone: 'warn' }
  return { text: '腰围在正常范围', tone: 'ok' }
})

// 减到正常上线的距离
const toNormal = computed(() => {
  if (!valid.value || !normalHigh.value) return null
  const d = w.value - normalHigh.value
  return d > 0.5 ? Math.round(d * 10) / 10 : 0
})

</script>

<template>
  <div class="calc">
    <div class="calc-bar">
      <span v-if="restored" class="kept">已经把你上次填的数填回来了</span>
      <span v-else class="kept">填一次就够了，下次打开自动填上</span>
      <button type="button" @click="reset">清空重填</button>
    </div>
    <div class="calc-grid">
      <label class="f">
        <span>性别</span>
        <select v-model="sex">
          <option value="male">男</option>
          <option value="female">女</option>
        </select>
      </label>
      <label class="f">
        <span>年龄（岁）</span>
        <input v-model.number="age" type="number" inputmode="numeric" min="18" max="100" />
      </label>
      <label class="f">
        <span>身高（厘米）</span>
        <input v-model.number="height" type="number" inputmode="decimal" />
      </label>
      <label class="f">
        <span>体重（公斤）</span>
        <input v-model.number="weight" type="number" inputmode="decimal" />
      </label>
      <label class="f wide">
        <span>平时活动量</span>
        <select v-model.number="activity">
          <option v-for="o in actOpts" :key="o.v" :value="o.v">{{ o.label }}</option>
        </select>
      </label>
      <label class="f">
        <span>腰围（厘米，可不填）</span>
        <input v-model.number="waist" type="number" inputmode="decimal" placeholder="按 2.8 的量法" />
      </label>
      <label class="f">
        <span>体脂率 %（可不填）</span>
        <input v-model.number="bodyFat" type="number" inputmode="decimal" placeholder="体脂秤上的数" />
      </label>
      <label class="f">
        <span>目标体重（公斤，可不填）</span>
        <input v-model.number="target" type="number" inputmode="decimal" placeholder="默认取正常上限" />
      </label>
      <label class="f check">
        <input v-model="pregnant" type="checkbox" />
        <span>怀孕或在哺乳</span>
      </label>
      <label class="f check wide">
        <input v-model="needsProfessional" type="checkbox" />
        <span>有基础病、正在用药、术后恢复或有进食障碍史</span>
      </label>
    </div>

    <p v-if="!canGuide" class="hint alert">
      {{ eligibilityReason }}
      <span v-if="valid">当前 BMI 约 {{ bmi.toFixed(1) }}。</span>
    </p>

    <div v-else class="out">
      <div class="row big">
        <div class="cell">
          <div class="k">你的 BMI</div>
          <div class="v">{{ bmi.toFixed(1) }}</div>
          <div class="tag" :class="bmiBand.tone">{{ bmiBand.text }}</div>
        </div>
        <div class="cell">
          <div class="k">正常区间</div>
          <div class="v small">{{ normalLow.toFixed(1) }}–{{ normalHigh.toFixed(1) }}</div>
          <div class="sub">公斤（BMI 18.5–23.9）</div>
        </div>
        <div class="cell">
          <div class="k">离正常上沿</div>
          <div class="v small">{{ toNormal === 0 ? '已经在区间里' : toNormal + ' 公斤' }}</div>
          <div class="sub">{{ toNormal === 0 ? '不用减，去练' : '不是必须减到这个数' }}</div>
        </div>
      </div>

      <div class="row">
        <div class="cell">
          <div class="k">静息消耗估值 REE</div>
          <div class="v">{{ Math.round(bmr) }}</div>
          <div class="sub">千卡／天，躺着不动也要烧</div>
        </div>
        <div class="cell">
          <div class="k">一天总消耗 TDEE</div>
          <div class="v">{{ Math.round(tdee) }}</div>
          <div class="sub">静息消耗估值 × 活动系数 {{ activity }}</div>
        </div>
        <div class="cell hl">
          <div class="k">参考摄入量</div>
          <div class="v">{{ Math.round(intake) }}</div>
          <div class="sub">千卡，约 {{ portions.toFixed(1) }} 份（一份 90 千卡）</div>
        </div>
      </div>

      <div class="row">
        <div class="cell">
          <div class="k">每天缺口</div>
          <div class="v">{{ Math.round(deficit) }}</div>
          <div class="sub">千卡</div>
        </div>
        <div v-if="protein" class="cell">
          <div class="k">蛋白质演算参考</div>
          <div class="v small">{{ protein.low }}–{{ protein.high }} 克</div>
          <div class="sub">按目标体重 {{ targetWeight }} 公斤 × 1.2～1.6</div>
        </div>
      </div>
      <p v-if="!protein" class="hint warn">
        目标体重需在成人正常区间下沿以上，且不高于当前体重；此时不计算蛋白质目标。
      </p>

      <p v-if="floored" class="hint warn">
        按本书的演算约定，参考摄入量以静息消耗估值兜底，纸面缺口约
        {{ Math.round(deficit) }} 千卡。这不是安全保证，也不必为了凑满 500 而少吃或直接提高活动系数。
      </p>
      <p v-if="deficit < 200" class="hint warn">
        低活动量的人可能得到较小缺口，不必硬凑整。是否调整，要结合数周记录、营养和身体反应。
      </p>

      <div v-if="waistBand" class="inline-tag">
        腰围 {{ waist }} 厘米：<span class="tag" :class="waistBand.tone">{{ waistBand.text }}</span>
      </div>

      <div v-if="ffm" class="hint">
        你填了体脂率 {{ bodyFat }}%：去脂体重约 {{ ffm.lean.toFixed(1) }} 公斤。按去脂体重公式估算的静息消耗是
        {{ Math.round(ffm.bmr) }} 千卡，跟上面的 {{ Math.round(bmr) }} 差了
        {{ Math.round(Math.abs(ffm.bmr - bmr)) }} 千卡。体脂越偏离一般人，两个式子差得越多；体脂秤本身也不准，拿不准就用上面那个。
      </div>

      <div class="note">
        <strong>这些数是从哪来的。</strong>
        静息消耗用 Mifflin-St Jeor 公式〔R8〕；TDEE 以估值乘活动系数，不能只按每周运动次数选档；
        BMI 分档按《成人体重判定》〔G8〕。G4 给出 1.2～1.6 克／公斤／天，改按目标体重只是本书演算约定；
        “减 500、以静息消耗估值兜底”是本书组合规则，不是 G1 的现成处方或安全保证；“一份 90 千卡”见 G1 附录 2。
      </div>
      <div class="note">
        <strong>这只是估算。</strong>
        公式用到个人时误差可能不小，不能把它看成实测。结合数周同条件体重、标准腰围、饮食和活动记录复核；
        不按短期体重差精确反推每日缺口，也不线性预报几周减几公斤。
        身体有基础病、在吃药、刚做完手术的，先看第八部分，这一页的数不能替医生。
      </div>
    </div>
  </div>
</template>

<style scoped>
.calc {
  border: 1px solid var(--vp-c-divider);
  border-radius: 12px;
  padding: 20px;
  margin: 24px 0;
  background: var(--vp-c-bg-soft);
}
.calc-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
  font-size: 13px;
  color: var(--vp-c-text-3);
}
.calc-bar button {
  flex: none;
  padding: 4px 12px;
  border: 1px solid var(--vp-c-divider);
  border-radius: 999px;
  background: transparent;
  color: var(--vp-c-text-2);
  font-size: 13px;
  cursor: pointer;
}
.calc-bar button:hover {
  border-color: var(--vp-c-brand-1);
  color: var(--vp-c-brand-1);
}
.calc-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px 16px;
}
.f {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 14px;
}
.f.wide { grid-column: 1 / -1; }
.f span { color: var(--vp-c-text-2); }
.f.check {
  flex-direction: row;
  align-items: center;
  gap: 8px;
}
.f.check span { color: var(--vp-c-text-1); }
input[type='number'],
select {
  padding: 7px 10px;
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  background: var(--vp-c-bg);
  color: var(--vp-c-text-1);
  font-size: 15px;
  width: 100%;
  box-sizing: border-box;
}
input[type='number']:focus,
select:focus {
  outline: 2px solid var(--vp-c-brand-1);
  outline-offset: 1px;
}
.hint {
  margin: 14px 0 0;
  font-size: 14px;
  line-height: 1.7;
  color: var(--vp-c-text-2);
  border-left: 3px solid var(--vp-c-divider);
  padding-left: 12px;
}
.hint.warn { border-left-color: #c08a3e; color: var(--vp-c-text-1); }
.hint.alert { border-left-color: #b0392b; color: var(--vp-c-text-1); }
.out { margin-top: 6px; }
.row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
  margin-top: 14px;
}
.cell {
  border: 1px solid var(--vp-c-divider);
  border-radius: 10px;
  padding: 12px 14px;
  background: var(--vp-c-bg);
}
.cell.hl { border-color: #b0392b; }
.k { font-size: 13px; color: var(--vp-c-text-2); }
.v {
  font-size: 30px;
  font-weight: 600;
  line-height: 1.2;
  margin-top: 2px;
  font-variant-numeric: tabular-nums;
}
.v.small { font-size: 20px; }
.sub { font-size: 12px; color: var(--vp-c-text-3); margin-top: 3px; line-height: 1.5; }
.tag {
  display: inline-block;
  margin-top: 4px;
  padding: 1px 8px;
  border-radius: 999px;
  font-size: 12px;
  border: 1px solid currentColor;
}
.tag.ok { color: #4a7a4a; }
.tag.warn { color: #c08a3e; }
.tag.alert { color: #b0392b; }
.inline-tag { margin-top: 14px; font-size: 14px; color: var(--vp-c-text-2); }
.note {
  margin-top: 16px;
  font-size: 13px;
  line-height: 1.75;
  color: var(--vp-c-text-2);
}
.note strong { color: var(--vp-c-text-1); }
@media (max-width: 640px) {
  .calc { padding: 14px; }
  .v { font-size: 26px; }
}
</style>
