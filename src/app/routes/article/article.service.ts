import slugify from 'slugify';
import prisma from '../../../prisma/prisma-client';
import HttpException from '../../models/http-exception.model';
import profileMapper from '../profile/profile.utils';
import articleMapper from './article.mapper';
import { Tag } from '../tag/tag.model';

const isFavorited = (favoritedByIds: string[], userId: string) => favoritedByIds.includes(userId);

export const getArticles = async (query: any, id?: string) => {
  const articlesCount = await prisma.article.count();
  const articles = await prisma.article.findMany({
    orderBy: { createdAt: 'desc' },
    skip: Number(query.offset) || 0,
    take: Number(query.limit) || 10,
    include: { tagList: true, author: true },
  });

  return {
    articles: articles.map((article: any) => ({
      ...article,
      favorited: id ? isFavorited(article.favoritedByIds, id) : false,
      favoritesCount: article.favoritedByIds.length,
      author: profileMapper(article.author, id),
    })),
    articlesCount,
  };
};

export const getArticle = async (slug: string, id?: string) => {
  const article = await prisma.article.findUnique({ where: { slug }, include: { tagList: true, author: true } });
  if (!article) throw new HttpException(404, { message: 'Artigo não encontrado' });
  return articleMapper(article, id);
};

export const createArticle = async (article: any, id: string) => {
  const { title, description, body, tagList } = article;
  const tags = Array.isArray(tagList) ? tagList : [];
  const slug = `${slugify(title)}-${Date.now()}`;

  const createdArticle = await prisma.article.create({
    data: {
      title, description, body, slug,
      tagList: { connectOrCreate: tags.map((name: string) => ({ create: { name }, where: { name } })) },
      authorId: id,
    },
    include: { tagList: true, author: true },
  });
  return articleMapper(createdArticle, id);
};

export const updateArticle = async (article: any, slug: string, id: string) => {
  const existingArticle = await prisma.article.findUnique({ where: { slug } });
  if (!existingArticle) throw new HttpException(404, {});
  if (existingArticle.authorId !== id) throw new HttpException(403, { message: 'Não autorizado' });

  const updatedArticle = await prisma.article.update({
    where: { slug },
    data: {
      ...(article.title ? { title: article.title, slug: `${slugify(article.title)}-${id}` } : {}),
      ...(article.body ? { body: article.body } : {}),
      ...(article.description ? { description: article.description } : {}),
      updatedAt: new Date(),
    },
    include: { tagList: true, author: true },
  });
  return articleMapper(updatedArticle, id);
};

export const deleteArticle = async (slug: string, id: string) => {
  const article = await prisma.article.findUnique({ where: { slug } });
  if (!article || article.authorId !== id) throw new HttpException(403, {});
  await prisma.article.delete({ where: { slug } });
};

export const favoriteArticle = async (slugPayload: string, id: string) => {
  const article = await prisma.article.update({
    where: { slug: slugPayload },
    data: { favoritedByIds: { push: id } },
    include: { tagList: true, author: true },
  });
  return { ...article, favorited: true, favoritesCount: article.favoritedByIds.length, author: profileMapper(article.author, id) };
};

export const unfavoriteArticle = async (slugPayload: string, id: string) => {
  const article = await prisma.article.findUnique({ where: { slug: slugPayload } });
  if (!article) throw new HttpException(404, {});
  const updatedArticle = await prisma.article.update({
    where: { slug: slugPayload },
    data: { favoritedByIds: { set: article.favoritedByIds.filter((uid) => uid !== id) } },
    include: { tagList: true, author: true },
  });
  return { ...updatedArticle, favorited: false, favoritesCount: updatedArticle.favoritedByIds.length, author: profileMapper(updatedArticle.author, id) };
};

export const addComment = async (id: string, comment: any, articleId: string) => {
  return await prisma.comment.create({
    data: { body: comment.body, authorId: id, articleId: articleId },
  });
};

export const getCommentsByArticle = async (slug: string) => {
  const article = await prisma.article.findUnique({ where: { slug } });
  return article ? await prisma.comment.findMany({ where: { articleId: article.id }, include: { author: true } }) : [];
};

export const deleteComment = async (commentId: string, userId: string) => {
  const comment = await prisma.comment.findUnique({ where: { id: commentId } });
  if (!comment || comment.authorId !== userId) throw new HttpException(403, {});
  await prisma.comment.delete({ where: { id: commentId } });
};

export const getFeed = async (id: string, query: any) => {
  // Implementação simplificada para feed
  return await getArticles(query, id);
};