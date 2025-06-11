import { SkeletonInterface } from '@/modules/common/components/Skeleton/interface'

export const Skeleton = ({ className, width, height }: SkeletonInterface) => {
  return (
    <div
      className={`rounded-lg animate-pulse bg-gray-600/75 ${className}`}
      style={{
        ...(width ? { width } : {}),
        ...(height ? { height } : {}),
      }}
    ></div>
  )
}
