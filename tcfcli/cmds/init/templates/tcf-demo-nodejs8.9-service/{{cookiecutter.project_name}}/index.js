const express = require('express')
const app = express()

app.get('/', (req, res) => res.send('Hello World!'))

const port = process.env.TENCENTCLOUD_SERVER_PORT || 8080
console.log('listening port',port)
app.listen(port, () => console.log('Example app listening on',port))
