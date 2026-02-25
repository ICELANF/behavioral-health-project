<template>
  <div class="page-container">
    <van-nav-bar title="关于我们" left-arrow @click-left="$router.back()" />

    <div class="page-content">
      <div class="card about-card">
        <div class="logo-section">
          <van-icon name="shield-o" size="64" color="#1989fa" />
          <h1>行健行为教练</h1>
          <p class="version">v{{ appVersion }}</p>
        </div>

        <div class="desc-section">
          <p>
            行健行为教练是一款专注于行为健康管理的智能平台。
            结合可穿戴设备数据、AI智能分析和专业教练指导，
            帮助用户建立健康的行为习惯，实现全方位的身心健康管理。
          </p>
        </div>

        <van-cell-group :border="false" class="info-group">
          <van-cell title="核心功能" value="行为评估 · AI教练 · 健康追踪" />
          <van-cell title="技术架构" value="FastAPI · Vue3 · AI引擎" />
          <van-cell title="数据安全" value="JWT认证 · HTTPS · 加密存储" />
          <van-cell title="设备支持" value="智能手表 · 手环 · 血糖仪 · 体脂秤" />
        </van-cell-group>

        <div class="team-section">
          <h3>平台特色</h3>
          <div class="feature-grid">
            <div class="feature-item">
              <van-icon name="friends-o" size="32" color="#1989fa" />
              <span>专业教练</span>
            </div>
            <div class="feature-item">
              <van-icon name="chart-trending-o" size="32" color="#07c160" />
              <span>数据驱动</span>
            </div>
            <div class="feature-item">
              <van-icon name="shield-o" size="32" color="#7c3aed" />
              <span>隐私保护</span>
            </div>
            <div class="feature-item">
              <van-icon name="smile-o" size="32" color="#ff976a" />
              <span>个性方案</span>
            </div>
          </div>
        </div>

        <div class="contact-section">
          <h3>联系我们</h3>
          <van-cell-group :border="false">
            <van-cell title="官方邮箱" value="contact@xingjian-health.com" icon="envelop-o" />
            <van-cell title="技术支持" value="support@xingjian-health.com" icon="service-o" />
          </van-cell-group>
        </div>

        <div class="copyright">
          &copy; 2026 行健健康科技 版权所有
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { APP_VERSION } from '@/config'
const appVersion = APP_VERSION
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.about-card {
  text-align: center;
}

.logo-section {
  padding: $spacing-lg 0;

  h1 {
    font-size: 22px;
    margin-top: $spacing-sm;
    color: $text-color;
  }

  .version {
    font-size: $font-size-sm;
    color: $text-color-secondary;
    margin-top: 4px;
  }
}

.desc-section {
  padding: 0 $spacing-md $spacing-lg;

  p {
    font-size: $font-size-md;
    line-height: 1.8;
    color: $text-color-secondary;
    text-align: left;
  }
}

.info-group {
  :deep(.van-cell-group) {
    background: transparent;
  }

  :deep(.van-cell__value) {
    font-size: $font-size-sm;
    color: $text-color-secondary;
  }
}

.team-section {
  margin-top: $spacing-lg;

  h3 {
    font-size: $font-size-lg;
    margin-bottom: $spacing-md;
  }

  .feature-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: $spacing-md;

    .feature-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: $spacing-xs;

      span {
        font-size: $font-size-xs;
        color: $text-color-secondary;
      }
    }
  }
}

.contact-section {
  margin-top: $spacing-lg;
  text-align: left;

  h3 {
    font-size: $font-size-lg;
    margin-bottom: $spacing-sm;
    text-align: center;
  }
}

.copyright {
  margin-top: $spacing-lg;
  font-size: $font-size-xs;
  color: $text-color-placeholder;
  padding-bottom: $spacing-md;
}
</style>
