const { default: makeWASocket, useMultiFileAuthState, DisconnectReason } = require('@whiskeysockets/baileys');
const qrcode = require('qrcode-terminal');
const pino = require('pino');
const axios = require('axios');
const fs = require('fs');
const path = require('path');

const URL_API_PYTHON = 'http://127.0.0.1:5000/chat';

// Define o caminho absoluto para a pasta de autenticação
const pastaAuth = path.resolve(__dirname, 'auth_info_baileys');

// Garante que a pasta existe antes de o Baileys inicializar
if (!fs.existsSync(pastaAuth)) {
    fs.mkdirSync(pastaAuth, { recursive: true });
}

async function iniciarBotWhatsApp() {
    // Usa o caminho absoluto criado
    const { state, saveCreds } = await useMultiFileAuthState(pastaAuth);

    const sock = makeWASocket({
        auth: state,
        logger: pino({ level: 'silent' }),
        printQRInTerminal: false
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

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('messages.upsert', async ({ messages, type }) => {
        if (type !== 'notify') return;

        for (const msg of messages) {
            if (msg.key.fromMe || msg.key.remoteJid.includes('@broadcast')) continue;

            const remetente = msg.key.remoteJid;
            const corpoMensagem = msg.message?.conversation || 
                                  msg.message?.extendedTextMessage?.text;

            if (!corpoMensagem) continue;

            console.log(`📩 Mensagem recebida de [${remetente}]: ${corpoMensagem}`);

            try {
                await sock.sendPresenceUpdate('composing', remetente);

                const response = await axios.post(URL_API_PYTHON, {
                    remetente: remetente,
                    mensagem: corpoMensagem
                });

                const respostaBot = response.data.resposta;

                await sock.sendPresenceUpdate('paused', remetente);
                await sock.sendMessage(remetente, { text: respostaBot });
                console.log(`📤 Resposta enviada para [${remetente}]`);

            } catch (error) {
                console.error('❌ Erro ao comunicar com a API Python:', error.message);
                await sock.sendMessage(remetente, {
                    text: 'Olá! Tivemos uma breve oscilação no sistema. Em breve nossa equipe retornará seu contato.'
                });
            }
        }
    });
}

iniciarBotWhatsApp();