/**
 * Main Entry Point - 主入口
 * 启动Metabolic Core API服务
 */

import 'reflect-metadata';
import { startServer } from './api/server';
import { orchestrator } from './orchestrator/Orchestrator';
import { initializeDatabase, closeDatabase } from './database';

async function main() {
  console.log('Starting Metabolic Core...');
  console.log('=====================================');
  console.log('  行健行为教练 - Metabolic Core');
  console.log('  代谢慢病行为健康决策系统内核');
  console.log('=====================================');

  try {
    // 初始化数据库连接
    console.log('\nInitializing Database...');
    await initializeDatabase();
    console.log('  - Database connected successfully');

    // 初始化编排器（这会加载所有知识库）
    console.log('\nInitializing Orchestrator...');
    await orchestrator.initialize();

    // 获取系统状态
    const status = orchestrator.getSystemStatus();
    console.log('\nSystem Status:');
    console.log(`  - Libraries Loaded: ${status.libraryStatus.filter(l => l.loaded).length}/${status.libraryStatus.length}`);
    console.log(`  - Total Knowledge Entries: ${status.overallStats.totalEntries}`);
    console.log(`  - Active Sessions: ${status.activeSessions}`);

    // 启动API服务器
    console.log('\nStarting API Server...');
    startServer();

    // 优雅关闭
    process.on('SIGINT', async () => {
      console.log('\nShutting down...');
      await closeDatabase();
      process.exit(0);
    });

    process.on('SIGTERM', async () => {
      console.log('\nShutting down...');
      await closeDatabase();
      process.exit(0);
    });

  } catch (error) {
    console.error('Failed to start Metabolic Core:', error);
    process.exit(1);
  }
}

// 运行主函数
main().catch(console.error);
