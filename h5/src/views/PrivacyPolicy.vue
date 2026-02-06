<template>
  <div class="page-container">
    <van-nav-bar title="隐私政策" left-arrow @click-left="$router.back()" />

    <div class="page-content">
      <div class="card policy-card">
        <h2>隐私政策</h2>
        <p class="update-time">最后更新：2026年1月1日</p>

        <section>
          <h3>一、信息收集</h3>
          <p>我们可能会收集以下类型的信息：</p>
          <ul>
            <li><strong>账号信息</strong>：用户名、邮箱、手机号码等注册信息。</li>
            <li><strong>健康数据</strong>：通过穿戴设备或手动录入的心率、步数、睡眠、血糖、血压、体重等健康指标。</li>
            <li><strong>行为评估</strong>：您完成的问卷评估结果，包括但不限于行为特质评估、心理健康筛查。</li>
            <li><strong>对话记录</strong>：您与AI教练之间的对话内容，用于改善服务质量。</li>
          </ul>
        </section>

        <section>
          <h3>二、信息使用</h3>
          <p>收集的信息将用于：</p>
          <ul>
            <li>为您提供个性化的行为健康管理建议。</li>
            <li>生成健康报告和趋势分析。</li>
            <li>优化AI教练的对话质量和准确性。</li>
            <li>平台功能改进和用户体验优化。</li>
          </ul>
        </section>

        <section>
          <h3>三、信息保护</h3>
          <p>我们采取以下措施保护您的信息安全：</p>
          <ul>
            <li>所有数据传输采用HTTPS加密协议。</li>
            <li>用户密码使用bcrypt算法加密存储，不可逆。</li>
            <li>认证令牌（JWT）具有有效期限制，登出后立即失效。</li>
            <li>严格的角色权限控制，确保数据访问范围最小化。</li>
            <li>定期安全审计和漏洞扫描。</li>
          </ul>
        </section>

        <section>
          <h3>四、信息共享</h3>
          <p>未经您的明确同意，我们不会将您的个人信息分享给第三方，但以下情况除外：</p>
          <ul>
            <li>经您授权的健康教练可查看您的健康数据和评估结果。</li>
            <li>法律法规要求披露的情况。</li>
            <li>为保护平台及其用户权益而必要的情况。</li>
          </ul>
        </section>

        <section>
          <h3>五、您的权利</h3>
          <ul>
            <li><strong>查阅权</strong>：您可随时查看自己的个人信息和健康数据。</li>
            <li><strong>更正权</strong>：您可修改不准确的个人信息。</li>
            <li><strong>删除权</strong>：您可申请删除个人账号及相关数据。</li>
            <li><strong>撤回同意</strong>：您可随时撤回对信息收集的同意。</li>
          </ul>
        </section>

        <section>
          <h3>六、联系我们</h3>
          <p>如有隐私相关的问题或建议，请联系我们：</p>
          <p>邮箱：privacy@xingjian-health.com</p>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.policy-card {
  h2 {
    font-size: 20px;
    text-align: center;
    margin-bottom: 4px;
  }

  .update-time {
    text-align: center;
    font-size: $font-size-sm;
    color: $text-color-secondary;
    margin-bottom: $spacing-lg;
  }

  section {
    margin-bottom: $spacing-lg;

    h3 {
      font-size: $font-size-lg;
      margin-bottom: $spacing-sm;
      color: $text-color;
    }

    p {
      font-size: $font-size-md;
      line-height: 1.8;
      color: $text-color;
    }

    ul {
      padding-left: 20px;
      margin-top: $spacing-xs;

      li {
        font-size: $font-size-md;
        line-height: 2;
        color: $text-color;
      }
    }
  }
}
</style>
