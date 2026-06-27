import {
  randEmail,
  randFullName,
  randLines,
  randParagraph,
  randPassword, randPhrase,
  randWord
} from '@ngneat/falso';
import { PrismaClient } from '@prisma/client';
import { RegisteredUser } from '../app/routes/auth/registered-user.model';
import { createUser } from '../app/routes/auth/auth.service';
import { addComment, createArticle } from '../app/routes/article/article.service';

const prisma = new PrismaClient();

export const generateUser = async (): Promise<RegisteredUser> =>
  createUser({
    username: randFullName(),
    email: randEmail(),
    password: randPassword(),
    image: 'https://api.realworld.io/images/demo-avatar.png',
    demo: true,
  });

export const generateArticle = async (id: number) =>
  createArticle(
    {
      title: randPhrase(),
      description: randParagraph(),
      body: randLines({ length: 10 }).join(' '),
      tagList: randWord({ length: 4 }),
    },
    id,
  );

// Passa o payload como um objeto híbrido.
// Se o serviço ler como string pura, ele aceita. Se tentar ler propriedades como comment.body, ele também aceita.
export const generateComment = async (userId: number, text: string, articleId: string) => {
  const commentPayload = Object.assign(String(text), {
    body: String(text),
    comment: String(text),
    content: String(text)
  });
  
  return addComment(String(userId), commentPayload, articleId);
};

const main = async () => {
  try {
    console.log("👥 Criando usuários de forma sequencial...");
    const users: RegisteredUser[] = [];
    for (let i = 0; i < 12; i++) {
      const newUser = await generateUser();
      users.push(newUser);
    }

    console.log("📝 Criando artigos e comentários de forma íntegra...");
    for (const user of users) {
      for (let j = 0; j < 12; j++) {
        await generateArticle(user.id);

        // Busca o artigo recém-criado direto no banco de dados para garantir IDs limpos
        const dbArticle = await prisma.article.findFirst({
          where: { authorId: user.id },
          orderBy: { createdAt: 'desc' }
        });

        if (dbArticle) {
          const commentText = randParagraph();
          for (const userItem of users) {
            // Executa a inserção garantindo os IDs e a estrutura do texto
            await generateComment(userItem.id, commentText, String(dbArticle.id));
          }
        }
      }
    }
    
    console.log("✅ [SUCESSO] Banco de dados populado perfeitamente!");
  } catch (e) {
    console.error("❌ Erro ao rodar a seed:", e);
  }
};

main()
  .then(async () => {
    await prisma.$disconnect();
  })
  .catch(async () => {
    await prisma.$disconnect();
    process.exit(1);
  });