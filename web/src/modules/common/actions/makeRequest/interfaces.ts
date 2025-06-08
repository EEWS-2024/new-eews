export interface MakeRequestInterface {
  path: string
  method: 'GET' | 'POST'
  body?: object
}
