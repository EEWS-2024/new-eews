'use server'

import axios, { AxiosError } from 'axios'
import { configKey } from '@/modules/common/configs'
import { MakeRequestInterface } from '@/modules/common/actions/makeRequest/interfaces'

export const makeRequest = async <T>({
  path,
  method,
  body,
}: MakeRequestInterface) => {
  try {
    const { data } = await axios<T>({
      url: `${configKey.serverUrl}/${path}`,
      method,
      data: body,
    })

    return data
  } catch (e: unknown) {
    if (e instanceof AxiosError) {
      throw new Error(e.response?.data.message)
    }
    throw new Error('Something went wrong')
  }
}
