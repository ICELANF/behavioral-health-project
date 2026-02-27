<template>
  <div ref="rootRef" class="landing-root" :data-page="currentPage">
    <!-- Nav -->
    <nav class="l-nav">
      <div class="l-nav-left">
        <div class="l-nav-logo" @click="go('home')"><span class="l-dot">●</span> BHP</div>
        <div class="l-nav-links">
          <button v-for="item in NAV_ITEMS" :key="item.key" class="l-nav-link" :class="{ active: currentPage === item.key }" @click="go(item.key)">{{ item.label }}</button>
        </div>
      </div>
      <button class="l-nav-cta" @click="openContact()">预约演示</button>
    </nav>

    <!-- Hero -->
    <section class="l-hero">
      <div class="l-hero-grid-overlay" />
      <div class="l-hero-glow1" /><div class="l-hero-glow2" />
      <div class="l-hero-inner">
        <div class="l-hero-grid">
          <div>
            <div class="l-hero-tag l-fade-in"><div class="l-pulse-dot" /><span>{{ pageData.heroTag }}</span></div>
            <h1 class="l-fade-in" style="transition-delay:.1s" v-html="sanitizeHtml(pageData.heroTitle)" />
            <p class="l-hero-subtitle l-fade-in" style="transition-delay:.2s">{{ pageData.heroSubtitle }}</p>
            <div class="l-hero-buttons l-fade-in" style="transition-delay:.3s">
              <button class="l-btn-primary" @click="openContact()">{{ pageData.heroCta }}</button>
              <button class="l-btn-ghost" @click="scrollToNext()">了解更多 →</button>
            </div>
            <div class="l-hero-stats l-fade-in" style="transition-delay:.4s">
              <div v-for="(s, i) in pageData.heroStats" :key="i">
                <div class="l-stat-val"><LandingCounter :target="s.value" :suffix="s.suffix" :key="currentPage + i" /></div>
                <div class="l-stat-label">{{ s.label }}</div>
              </div>
            </div>
          </div>
          <div class="l-hero-visual l-fade-left" style="transition-delay:.3s">
            <LandingHeroSVG :paths="svgData.paths" :nodes="svgData.nodes" :key="currentPage" />
          </div>
        </div>
      </div>
      <div class="l-hero-fade" />
    </section>

    <!-- Scene Cards (home only) -->
    <section ref="sectionScenesRef" v-if="pageData.hasScenes" class="l-section">
      <div class="l-inner">
        <div class="l-section-header l-fade-in">
          <div class="l-section-tag">解决方案</div>
          <h2 class="l-section-title">四大场景，一套底座</h2>
          <p class="l-section-sub">同一个AI引擎驱动不同场景，每个场景有独立的业务语言</p>
        </div>
        <div class="l-scene-grid">
          <div v-for="(s, i) in SCENES" :key="s.key" class="l-scene-card l-fade-in" :style="{ background: s.bg, color: s.color, transitionDelay: (i * 0.1) + 's' }" @click="go(s.key)">
            <div class="l-scene-icon">{{ s.icon }}</div>
            <h3>{{ s.title }}</h3>
            <div class="l-scene-desc">{{ s.desc }}</div>
            <div class="l-scene-sub">{{ s.sub }}</div>
            <div class="l-scene-arrow">探索方案 →</div>
          </div>
        </div>
      </div>
    </section>

    <!-- Flow -->
    <section ref="sectionFlowRef" class="l-section l-bg-gradient">
      <div class="l-inner">
        <div class="l-section-header l-fade-in">
          <div class="l-section-tag">{{ pageData.sectionTag }}</div>
          <h2 class="l-section-title">{{ pageData.sectionTitle }}</h2>
          <p class="l-section-sub">{{ pageData.sectionSub }}</p>
        </div>
        <div class="l-flow">
          <div v-for="(step, i) in pageData.flow" :key="i" class="l-flow-step l-fade-in" :style="{ transitionDelay: (i * 0.08) + 's' }">
            <div v-if="i < pageData.flow.length - 1" class="l-flow-line" />
            <div class="l-flow-circle">{{ step.icon }}</div>
            <div class="l-flow-title">{{ step.title }}</div>
            <div class="l-flow-desc">{{ step.desc }}</div>
          </div>
        </div>
      </div>
    </section>

    <!-- Data Cards -->
    <section ref="sectionCardsRef" class="l-section l-bg-white">
      <div class="l-inner">
        <div class="l-section-header l-fade-in">
          <div class="l-section-tag">{{ pageData.cardsTag }}</div>
          <h2 class="l-section-title">{{ pageData.cardsTitle }}</h2>
        </div>
        <div class="l-card-grid">
          <div v-for="(c, i) in pageData.cards" :key="i" class="l-data-card l-fade-in" :style="{ transitionDelay: (i * 0.08) + 's' }">
            <div class="l-card-icon">{{ c.icon }}</div>
            <div class="l-card-number"><LandingCounter :target="c.number" :suffix="c.suffix" :key="currentPage + '-card-' + i" /></div>
            <div class="l-card-label">{{ c.label }}</div>
            <div class="l-card-desc">{{ c.description }}</div>
          </div>
        </div>
      </div>
    </section>

    <!-- Testimonials -->
    <section ref="sectionTestimonialsRef" class="l-section l-bg-warm">
      <div class="l-inner">
        <div class="l-section-header l-fade-in">
          <div class="l-section-tag">客户声音</div>
          <h2 class="l-section-title">从使用者那里听到的</h2>
        </div>
        <div class="l-quote-grid">
          <div v-for="(q, i) in pageData.testimonials" :key="i" class="l-quote-card l-fade-in" :style="{ transitionDelay: (i * 0.08) + 's' }">
            <div class="l-quote-mark">"</div>
            <p>{{ q.quote }}</p>
            <div class="l-quote-author">
              <div class="l-quote-avatar" />
              <div><div class="l-quote-name">{{ q.name }}</div><div class="l-quote-role">{{ q.role }}</div></div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="l-cta">
      <div class="l-cta-grid-bg" />
      <div class="l-cta-inner l-fade-in">
        <h2>{{ pageData.cta.title }}</h2>
        <p>{{ pageData.cta.subtitle }}</p>
        <button class="l-cta-btn" @click="openContact()">{{ pageData.cta.button }}</button>
      </div>
    </section>

    <!-- Footer -->
    <footer class="l-footer">
      <div class="l-footer-grid">
        <div>
          <div class="l-footer-brand"><span style="color:#22c55e">●</span> BHP</div>
          <p class="l-footer-tagline">行为健康数字基建<br>让健康管理自然生长</p>
        </div>
        <div v-for="col in FOOTER_COLS" :key="col.title">
          <div class="l-footer-col-title">{{ col.title }}</div>
          <div v-for="item in col.items" :key="item" class="l-footer-link" @click="handleFooterLink(item)">{{ item }}</div>
        </div>
      </div>
      <div class="l-footer-bottom">
        <span>© 2026 行为健康促进专业委员会</span>
        <span>京ICP备XXXXXXXX号</span>
      </div>
    </footer>

    <!-- Contact Modal -->
    <div v-if="showContact" class="l-modal-mask" @click.self="showContact = false">
      <div class="l-modal">
        <div class="l-modal-header">
          <h3>预约演示</h3>
          <button class="l-modal-close" @click="showContact = false">&times;</button>
        </div>
        <!-- Success state -->
        <div v-if="submitResult.status === 'success'" class="l-modal-result l-result-success">
          <div class="l-result-icon">&#10003;</div>
          <h4>预约信息已提交</h4>
          <p>我们将尽快与您联系，感谢您的关注！</p>
          <button class="l-form-submit" @click="showContact = false">关闭</button>
        </div>
        <!-- Error state -->
        <div v-else-if="submitResult.status === 'error'" class="l-modal-result l-result-error">
          <div class="l-result-icon">!</div>
          <p>{{ submitResult.message }}</p>
          <button class="l-form-submit" @click="submitResult.status = ''">重新填写</button>
        </div>
        <!-- Form -->
        <form v-else class="l-modal-form" @submit.prevent="submitContact">
          <div class="l-form-row">
            <label>姓名 <span class="l-required">*</span></label>
            <input v-model="form.name" required placeholder="您的姓名" maxlength="50" />
          </div>
          <div class="l-form-row">
            <label>机构/公司</label>
            <input v-model="form.organization" placeholder="机构或公司名称" maxlength="200" />
          </div>
          <div class="l-form-row">
            <label>职位</label>
            <input v-model="form.title" placeholder="您的职位" maxlength="100" />
          </div>
          <div class="l-form-row">
            <label>手机 <span class="l-required">*</span></label>
            <input v-model="form.phone" required placeholder="联系电话" maxlength="20" />
          </div>
          <div class="l-form-row">
            <label>邮箱</label>
            <input v-model="form.email" type="email" placeholder="电子邮箱" maxlength="100" />
          </div>
          <div class="l-form-row">
            <label>感兴趣方案</label>
            <select v-model="form.solution">
              <option value="">请选择</option>
              <option value="hospital">医院</option>
              <option value="insurance">商保</option>
              <option value="government">政府</option>
              <option value="rwe">RWE</option>
            </select>
          </div>
          <div class="l-form-row">
            <label>备注</label>
            <textarea v-model="form.message" placeholder="请描述您的需求或问题" maxlength="2000" rows="3"></textarea>
          </div>
          <button type="submit" class="l-form-submit" :disabled="submitting">
            {{ submitting ? '提交中...' : '提交预约' }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, nextTick, type Ref } from 'vue'
import { useLandingTheme, useScrollReveal, SCENES, type PageData } from '../composables/useLanding'
import LandingHeroSVG from '../components/landing/LandingHeroSVG.vue'
import LandingCounter from '../components/landing/LandingCounter.vue'
import { sanitizeHtml } from '@/utils/sanitize'

const NAV_ITEMS = [
  { key: 'home', label: '首页' },
  { key: 'hospital', label: '医院' },
  { key: 'insurance', label: '商保' },
  { key: 'government', label: '政府' },
  { key: 'rwe', label: 'RWE' },
]

const FOOTER_COLS = [
  { title: '解决方案', items: ['医院', '商保', '政府', 'RWE'] },
  { title: '平台能力', items: ['BAPS评估', 'AI Agent', '知识引擎', '问卷系统'] },
  { title: '关于', items: ['团队', '研究', '联系我们', '加入我们'] },
]

const rootRef = ref<HTMLElement | null>(null)
const sectionScenesRef = ref<HTMLElement | null>(null)
const sectionFlowRef = ref<HTMLElement | null>(null)
const sectionCardsRef = ref<HTMLElement | null>(null)
const sectionTestimonialsRef = ref<HTMLElement | null>(null)

const { currentPage, theme, pageData, svgData, switchPage } = useLandingTheme()
const { reinit } = useScrollReveal(rootRef)

function go(page: string) {
  switchPage(page)
  nextTick(reinit)
}

// ── Smooth scroll ──
function scrollToEl(el: HTMLElement | null) {
  el?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function scrollToNext() {
  // 首页 → 场景卡片; 子页面 → 流程区
  if (currentPage.value === 'home') {
    scrollToEl(sectionScenesRef.value)
  } else {
    scrollToEl(sectionFlowRef.value)
  }
}

// ── Contact modal ──
const SOLUTION_MAP: Record<string, string> = {
  home: '', hospital: 'hospital', insurance: 'insurance', government: 'government', rwe: 'rwe',
}

const showContact = ref(false)
const submitting = ref(false)
const submitResult = reactive({ status: '', message: '' })
const form = reactive({
  name: '', organization: '', title: '', phone: '', email: '',
  solution: '', message: '',
})

function openContact(prefillMessage?: string) {
  form.solution = SOLUTION_MAP[currentPage.value] || ''
  if (prefillMessage) form.message = prefillMessage
  submitResult.status = ''
  submitResult.message = ''
  showContact.value = true
}

async function submitContact() {
  submitting.value = true
  try {
    const res = await fetch('/api/v1/demo-requests', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...form, source_page: currentPage.value }),
    })
    if (res.ok) {
      submitResult.status = 'success'
      Object.assign(form, { name: '', organization: '', title: '', phone: '', email: '', solution: '', message: '' })
    } else {
      const err = await res.json().catch(() => null)
      submitResult.status = 'error'
      submitResult.message = err?.detail || '提交失败，请稍后再试'
    }
  } catch {
    submitResult.status = 'error'
    submitResult.message = '网络错误，请检查网络后再试'
  } finally {
    submitting.value = false
  }
}

// ── Footer links ──
function handleFooterLink(item: string) {
  const pageMap: Record<string, string> = { '医院': 'hospital', '商保': 'insurance', '政府': 'government', 'RWE': 'rwe' }
  if (pageMap[item]) { go(pageMap[item]); return }

  const scrollMap: Record<string, Ref<HTMLElement | null>> = {
    'BAPS评估': sectionCardsRef, 'AI Agent': sectionCardsRef,
    '知识引擎': sectionCardsRef, '问卷系统': sectionCardsRef,
    '团队': sectionTestimonialsRef, '研究': sectionTestimonialsRef,
  }
  if (scrollMap[item]) { scrollToEl(scrollMap[item].value); return }

  if (item === '联系我们') { openContact(); return }
  if (item === '加入我们') { openContact('人才加入咨询'); return }
}
</script>

<style src="../assets/landing.scss"></style>
