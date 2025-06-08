import { SkeletonInterface } from '@/modules/common/components/Skeleton/interface'
import { twMerge } from 'tailwind-merge'

export const Skeleton = ({ className, width, height }: SkeletonInterface) => {
  return (
    <div
      className={twMerge('rounded-lg animate-pulse bg-gray-600/75', className)}
      style={{
        ...(width ? { width } : {}),
        ...(height ? { height } : {}),
      }}
    ></div>
  )
}
