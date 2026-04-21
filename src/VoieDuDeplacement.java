public class VoieDuDeplacement extends Voie {
    public VoieDuDeplacement() {
        super("Voie du deplacement");
        competences.add(new Competence("Esquive", 1));
        competences.add(new Competence("Chute", 2));
        competences.add(new Competence("Acrobaties", 3));
        competences.add(new Competence("Esquive de la magie", 4));
    }
}
