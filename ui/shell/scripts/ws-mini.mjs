/**
 * Minimal WebSocket client for CDP over localhost (no npm dependency).
 * Text frames only, no fragmentation handling beyond CDP's typical sizes,
 * client-side masking as required by RFC 6455.
 */
import { connect } from 'node:net'
import { randomBytes, createHash } from 'node:crypto'

export default class MiniWS {
  constructor(url) {
    this.url = new URL(url)
    this.handlers = []
    this.buffer = Buffer.alloc(0)
  }

  open() {
    return new Promise((resolve, reject) => {
      const key = randomBytes(16).toString('base64')
      this.sock = connect(Number(this.url.port), this.url.hostname, () => {
        this.sock.write(
          `GET ${this.url.pathname}${this.url.search} HTTP/1.1\r\n` +
            `Host: ${this.url.host}\r\n` +
            `Upgrade: websocket\r\nConnection: Upgrade\r\n` +
            `Sec-WebSocket-Key: ${key}\r\nSec-WebSocket-Version: 13\r\n\r\n`,
        )
      })
      this.sock.on('error', reject)
      let upgraded = false
      this.sock.on('data', (chunk) => {
        if (!upgraded) {
          const text = chunk.toString('latin1')
          const headerEnd = text.indexOf('\r\n\r\n')
          if (headerEnd === -1) return
          const accept = createHash('sha1')
            .update(key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11')
            .digest('base64')
          if (!text.includes(accept)) {
            reject(new Error('WS handshake failed'))
            return
          }
          upgraded = true
          this.buffer = chunk.subarray(headerEnd + 4)
          this.#drain()
          resolve()
          return
        }
        this.buffer = Buffer.concat([this.buffer, chunk])
        this.#drain()
      })
    })
  }

  #drain() {
    for (;;) {
      if (this.buffer.length < 2) return
      const b0 = this.buffer[0]
      const b1 = this.buffer[1]
      const opcode = b0 & 0x0f
      let len = b1 & 0x7f
      let offset = 2
      if (len === 126) {
        if (this.buffer.length < 4) return
        len = this.buffer.readUInt16BE(2)
        offset = 4
      } else if (len === 127) {
        if (this.buffer.length < 10) return
        len = Number(this.buffer.readBigUInt64BE(2))
        offset = 10
      }
      if (this.buffer.length < offset + len) return
      const payload = this.buffer.subarray(offset, offset + len)
      this.buffer = this.buffer.subarray(offset + len)
      if (opcode === 1) {
        const text = payload.toString('utf8')
        for (const h of this.handlers) h(text)
      } else if (opcode === 9) {
        this.#frame(10, payload) // pong
      } else if (opcode === 8) {
        this.sock.destroy()
        return
      }
    }
  }

  #frame(opcode, payload) {
    const mask = randomBytes(4)
    const masked = Buffer.from(payload)
    for (let i = 0; i < masked.length; i++) masked[i] ^= mask[i % 4]
    let header
    if (payload.length < 126) {
      header = Buffer.from([0x80 | opcode, 0x80 | payload.length])
    } else if (payload.length < 65536) {
      header = Buffer.alloc(4)
      header[0] = 0x80 | opcode
      header[1] = 0x80 | 126
      header.writeUInt16BE(payload.length, 2)
    } else {
      header = Buffer.alloc(10)
      header[0] = 0x80 | opcode
      header[1] = 0x80 | 127
      header.writeBigUInt64BE(BigInt(payload.length), 2)
    }
    this.sock.write(Buffer.concat([header, mask, masked]))
  }

  send(text) {
    this.#frame(1, Buffer.from(text, 'utf8'))
  }

  onMessage(fn) {
    this.handlers.push(fn)
  }
}
