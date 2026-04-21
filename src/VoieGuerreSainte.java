public class VoieGuerreSainte extends Voie {
    public VoieGuerreSainte() {
        super("Voie de la guerre sainte");
        competences.add(new Competence("Arme benie", 1));
        competences.add(new Competence("Bouclier de foi", 2));
        competences.add(new Competence("Marteau spirituel", 3));
        competences.add(new Competence("Chatiment divin", 4));
    }
}
