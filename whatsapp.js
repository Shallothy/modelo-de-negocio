const { default: makeWASocket, useMultiFileAuthState, DisconnectReason } = require('@whiskeysockets/baileys');
const qrcode = require('qrcode-terminal');
const pino = require('pino');
const axios = require('axios');
const path = require('path');
const fs = require('fs');

const URL_API_PYTHON = 'http://127.0.0.1:5000/chat';
const pastaAuth = path.join(__dirname, 'auth_info_baileys');

if (!fs.existsSync(pastaAuth)) {
    fs.mkdirSync(pastaAuth, { recursive: true });
}

function extrairTexto(msg) {
    if (!msg.message) return null;
    
    const conteudo = msg.message.ephemeralMessage?.message || msg.message;
    
    return conteudo.conversation || 
           conteudo.extendedTextMessage?.text || 
           conteudo.imageMessage?.caption || 
           null;
}

async function iniciarBotWhatsApp() {
    const { state, saveCreds } = await useMultiFileAuthState(pastaAuth);

    const sock = makeWASocket({
        auth: state,
        logger: pino({ level: 'silent' }),
        printQRInTerminal: false,
        browser: ['GRJ Secretária', 'Chrome', '1.0.0'],
        syncFullHistory: false
    });

    sock.ev.on('connection.update', (update) => {
        const { connection, lastDisconnect, qr } = update;

        if (qr) {
            console.log("\n📲 Escaneie o QR Code abaixo com o WhatsApp do seu bot:\n");
            qrcode.generate(qr, { small: true });
        }

        if (connection === 'close') {
            const statusCode = lastDisconnect?.error?.output?.statusCode;
            const shouldReconnect = statusCode !== DisconnectReason.loggedOut;
            console.log('Conexão fechada. Reconectando...', shouldReconnect);
            if (shouldReconnect) {
                iniciarBotWhatsApp();
            }
        } else if (connection === 'open') {
            console.log('✅ WhatsApp conectado com sucesso! Secretária GRJ pronta para atender.');
        }
    });

    sock.ev.on('creds.update', async () => {
        try {
            await saveCreds();
        } catch (err) {
        }
    });

    sock.ev.on('messages.upsert', async ({ messages, type }) => {
        if (type !== 'notify') return;

        for (const msg of messages) {
            if (msg.key.fromMe) continue;

            const remetente = msg.key.remoteJid || '';

            const ehGrupo = remetente.endsWith('@g.us');
            const ehStatusOuCanal = remetente.includes('@broadcast') || remetente.includes('@newsletter');

            if (ehGrupo || ehStatusOuCanal) {
                continue;
            }

            const corpoMensagem = extrairTexto(msg);
            if (!corpoMensagem) continue;

            console.log(`\n📩 [PRIVADO] Mensagem recebida de [${remetente}]: "${corpoMensagem}"`);

            try {
                await sock.sendPresenceUpdate('composing', remetente);

                const response = await axios.post(URL_API_PYTHON, {
                    remetente: remetente,
                    mensagem: corpoMensagem
                });

                const respostaBot = response.data.resposta;

                await sock.sendPresenceUpdate('paused', remetente);

                await sock.sendMessage(remetente, { text: respostaBot });
                console.log(`📤 Resposta da Secretária enviada com sucesso!`);

            } catch (error) {
                console.error('❌ Erro ao chamar a API Python:', error.message);
                await sock.sendMessage(remetente, {
                    text: 'Olá! Tivemos uma breve oscilação técnica. Em instantes retornaremos seu contato.'
                });
            }
        }
    });
}

iniciarBotWhatsApp().catch(err => {
    console.error('Erro fatal na inicialização:', err);
});