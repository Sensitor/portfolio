public class VoieDeLArcher extends Voie {
    public VoieDeLArcher() {
        super("Voie de l'archer");
        competences.add(new Competence("Sens affutes", 1));
        competences.add(new Competence("Tir aveugle", 2));
        competences.add(new Competence("Tir rapide", 3));
        competences.add(new Competence("Fleche de mort", 4));
    }
}
