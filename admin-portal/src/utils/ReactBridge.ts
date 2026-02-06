// ============================================================
// ReactBridge.ts - React组件在Vue中渲染的通用桥接器
// 位置: src/utils/ReactBridge.ts
// ============================================================

import { createApp, defineComponent, h, onMounted, onUnmounted, ref, watch, PropType } from 'vue'
import { createRoot, Root } from 'react-dom/client'
import React from 'react'

/**
 * 创建一个Vue组件包装器，用于渲染React组件
 * @param ReactComponent - React组件
 * @param componentName - 组件名称（用于调试）
 */
export function createReactWrapper<P extends object>(
  ReactComponent: React.ComponentType<P>,
  componentName: string = 'ReactComponent'
) {
  return defineComponent({
    name: `${componentName}Wrapper`,
    
    props: {
      // 传递给React组件的props
      reactProps: {
        type: Object as PropType<P>,
        default: () => ({}),
      },
      // 容器类名
      containerClass: {
        type: String,
        default: '',
      },
    },
    
    emits: ['mounted', 'unmounted', 'error'],
    
    setup(props, { emit }) {
      const containerRef = ref<HTMLDivElement | null>(null)
      let reactRoot: Root | null = null
      
      // 渲染React组件
      const renderReact = () => {
        if (!containerRef.value) return
        
        try {
          if (!reactRoot) {
            reactRoot = createRoot(containerRef.value)
          }
          
          // 使用React.createElement渲染组件
          reactRoot.render(
            React.createElement(ReactComponent, props.reactProps as P)
          )
        } catch (error) {
          console.error(`[ReactBridge] Error rendering ${componentName}:`, error)
          emit('error', error)
        }
      }
      
      // 挂载时渲染
      onMounted(() => {
        renderReact()
        emit('mounted')
      })
      
      // 卸载时清理
      onUnmounted(() => {
        if (reactRoot) {
          reactRoot.unmount()
          reactRoot = null
        }
        emit('unmounted')
      })
      
      // 监听props变化，重新渲染
      watch(
        () => props.reactProps,
        () => {
          renderReact()
        },
        { deep: true }
      )
      
      return () => h('div', {
        ref: containerRef,
        class: ['react-component-container', props.containerClass],
        'data-react-component': componentName,
      })
    },
  })
}

/**
 * 创建带有事件处理的React包装器
 */
export function createReactWrapperWithEvents<P extends object, E extends Record<string, (...args: any[]) => void>>(
  ReactComponent: React.ComponentType<P & E>,
  componentName: string,
  eventNames: (keyof E)[]
) {
  return defineComponent({
    name: `${componentName}Wrapper`,
    
    props: {
      reactProps: {
        type: Object as PropType<Omit<P, keyof E>>,
        default: () => ({}),
      },
      containerClass: {
        type: String,
        default: '',
      },
    },
    
    emits: ['mounted', 'unmounted', 'error', ...eventNames as string[]],
    
    setup(props, { emit }) {
      const containerRef = ref<HTMLDivElement | null>(null)
      let reactRoot: Root | null = null
      
      const renderReact = () => {
        if (!containerRef.value) return
        
        try {
          if (!reactRoot) {
            reactRoot = createRoot(containerRef.value)
          }
          
          // 创建事件处理器
          const eventHandlers: Partial<E> = {}
          for (const eventName of eventNames) {
            (eventHandlers as any)[eventName] = (...args: any[]) => {
              emit(eventName as string, ...args)
            }
          }
          
          // 合并props和事件处理器
          const combinedProps = {
            ...props.reactProps,
            ...eventHandlers,
          } as P & E
          
          reactRoot.render(
            React.createElement(ReactComponent, combinedProps)
          )
        } catch (error) {
          console.error(`[ReactBridge] Error rendering ${componentName}:`, error)
          emit('error', error)
        }
      }
      
      onMounted(() => {
        renderReact()
        emit('mounted')
      })
      
      onUnmounted(() => {
        if (reactRoot) {
          reactRoot.unmount()
          reactRoot = null
        }
        emit('unmounted')
      })
      
      watch(
        () => props.reactProps,
        () => renderReact(),
        { deep: true }
      )
      
      return () => h('div', {
        ref: containerRef,
        class: ['react-component-container', props.containerClass],
        'data-react-component': componentName,
      })
    },
  })
}
