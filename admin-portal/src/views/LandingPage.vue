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
      <button class="l-nav-cta">预约演示</button>
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
              <button class="l-btn-primary">{{ pageData.heroCta }}</button>
              <button class="l-btn-ghost">了解更多 →</button>
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
    <section v-if="pageData.hasScenes" class="l-section">
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
    <section class="l-section l-bg-gradient">
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
    <section class="l-section l-bg-white">
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
    <section class="l-section l-bg-warm">
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
        <button class="l-cta-btn">{{ pageData.cta.button }}</button>
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
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
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
const { currentPage, theme, pageData, svgData, switchPage } = useLandingTheme()
const { reinit } = useScrollReveal(rootRef)

function go(page: string) {
  switchPage(page)
  nextTick(reinit)
}

function handleFooterLink(item: string) {
  const map: Record<string, string> = { '医院': 'hospital', '商保': 'insurance', '政府': 'government', 'RWE': 'rwe' }
  if (map[item]) go(map[item])
}
</script>

<style src="../assets/landing.scss"></style>
